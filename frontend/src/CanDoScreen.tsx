import { useState, type FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ActionIcon, Autocomplete, Badge, Button, Group, Paper, SimpleGrid, Stack, Text, TextInput, Textarea } from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import { IconCircleCheck, IconPencil, IconPlus, IconSearch, IconTools } from '@tabler/icons-react'
import { EmptyState, ErrorBanner, Field, LoadingSpinner, Modal, PageHead, useAuth, useNav, useT, useToast } from '@hubra/plugin-sdk'
import { addMine, confirmCanDo, deleteMine, listCanDo, listKinds, unconfirmCanDo, updateMine, type CanDo } from './api'

const KEY = ['qualifications', 'canDo']

/** Who in the club can do what: the self-service qualifications. */
export function CanDoScreen() {
  const { t } = useT()
  const { hasPermission, currentUser } = useAuth()
  const me = currentUser ? Number(currentUser.id) : null
  const manager = hasPermission('qualifications.members.manage')
  const qc = useQueryClient()
  const { notify } = useToast()
  const [busyId, setBusyId] = useState<number | null>(null)
  const vouch = async (c: CanDo, on: boolean) => {
    setBusyId(c.id)
    try {
      await (on ? confirmCanDo(c.id) : unconfirmCanDo(c.id))
      qc.invalidateQueries({ queryKey: ['qualifications'] })
    } catch (err) {
      notify('error', err instanceof Error ? err.message : String(err))
    } finally {
      setBusyId(null)
    }
  }
  const { go } = useNav()
  const [q, setQ] = useState('')
  const [search] = useDebouncedValue(q.trim(), 250)
  const list = useQuery({ queryKey: [...KEY, search], queryFn: () => listCanDo(search) })
  const [editing, setEditing] = useState<CanDo | 'new' | null>(null)

  return (
    <>
      <PageHead
        title={t('qualifications.canDo.title')}
        desc={t('qualifications.canDo.desc')}
        actions={
          <Group gap="xs">
            {manager && (
              <Button variant="default" onClick={() => go('/app/qualifications')}>
                {t('qualifications.canDo.manage')}
              </Button>
            )}
            <Button leftSection={<IconPlus size={16} />} onClick={() => setEditing('new')}>
              {t('qualifications.canDo.add')}
            </Button>
          </Group>
        }
      />
      <TextInput
        leftSection={<IconSearch size={16} />}
        placeholder={t('qualifications.canDo.search')}
        value={q}
        onChange={(e) => setQ(e.currentTarget.value)}
        mb="md"
        maw={360}
      />
      {list.error ? (
        <ErrorBanner message={(list.error as Error).message} onRetry={() => list.refetch()} />
      ) : list.isLoading ? (
        <LoadingSpinner />
      ) : !list.data?.length ? (
        <EmptyState
          icon={<IconTools size={28} />}
          title={search ? t('qualifications.canDo.noMatch') : t('qualifications.canDo.none')}
          description={search ? undefined : t('qualifications.canDo.noneHint')}
        />
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="sm">
          {list.data.map((c) => (
            <Paper key={c.id} withBorder radius="md" p="md">
              <Group justify="space-between" wrap="nowrap" align="flex-start" gap="xs">
                <Stack gap={4} style={{ minWidth: 0 }}>
                  <Group gap={6} wrap="nowrap">
                    <Text fw={700} truncate>
                      {c.kindName}
                    </Text>
                    {c.mine && (
                      <Badge size="sm" variant="light" color="violet" style={{ textTransform: 'none', flexShrink: 0 }}>
                        {t('qualifications.canDo.you')}
                      </Badge>
                    )}
                  </Group>
                  {c.note && (
                    <Text size="sm" c="dimmed" lineClamp={3}>
                      {c.note}
                    </Text>
                  )}
                  <Text size="sm">{c.memberName}</Text>
                  {c.confirmedBy ? (
                    <Group gap={4} wrap="wrap">
                      <IconCircleCheck size={14} color="var(--mantine-color-green-6)" style={{ flexShrink: 0 }} />
                      <Text size="xs" c="dimmed">
                        {t('qualifications.canDo.confirmedBy', { name: c.confirmedBy })}
                      </Text>
                      {(c.confirmedById === me || (manager && !c.mine)) && (
                        <Button size="compact-xs" variant="subtle" color="gray" loading={busyId === c.id} onClick={() => vouch(c, false)}>
                          {t('qualifications.canDo.unconfirm')}
                        </Button>
                      )}
                    </Group>
                  ) : (
                    !c.mine && (
                      <Button
                        size="compact-xs"
                        variant="light"
                        leftSection={<IconCircleCheck size={14} />}
                        loading={busyId === c.id}
                        onClick={() => vouch(c, true)}
                        style={{ alignSelf: 'flex-start' }}
                      >
                        {t('qualifications.canDo.confirm')}
                      </Button>
                    )
                  )}
                </Stack>
                {c.mine && (
                  <ActionIcon variant="subtle" onClick={() => setEditing(c)} aria-label={t('qualifications.canDo.edit')}>
                    <IconPencil size={16} />
                  </ActionIcon>
                )}
              </Group>
            </Paper>
          ))}
        </SimpleGrid>
      )}
      {editing && <CanDoModal entry={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />}
    </>
  )
}

/** Add something I can do, or change its note, or remove it. */
export function CanDoModal({ entry, onClose }: { entry: Pick<CanDo, 'id' | 'kindName' | 'note'> | null; onClose: () => void }) {
  const { t } = useT()
  const qc = useQueryClient()
  const { notify } = useToast()
  const kinds = useQuery({ queryKey: ['qualifications', 'kinds'], queryFn: listKinds, enabled: !entry })
  const [name, setName] = useState('')
  const [note, setNote] = useState(entry?.note ?? '')
  const [busy, setBusy] = useState(false)
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true)
    try {
      await fn()
      qc.invalidateQueries({ queryKey: ['qualifications'] })
      onClose()
    } catch (err) {
      notify('error', err instanceof Error ? err.message : String(err))
    } finally {
      setBusy(false)
    }
  }
  const submit = (e?: FormEvent) => {
    e?.preventDefault()
    const text = note.trim() || null
    run(() => (entry ? updateMine(entry.id, text) : addMine({ name: name.trim(), note: text })))
  }
  return (
    <Modal
      open
      onClose={onClose}
      onSubmit={submit}
      title={entry ? entry.kindName : t('qualifications.canDo.add')}
      footer={
        <Group justify="space-between" w="100%">
          <div>
            {entry && (
              <Button variant="subtle" color="red" onClick={() => run(() => deleteMine(entry.id))}>
                {t('qualifications.remove')}
              </Button>
            )}
          </div>
          <Group gap="xs">
            <Button variant="default" onClick={onClose}>
              {t('qualifications.canDo.cancel')}
            </Button>
            <Button type="submit" loading={busy} disabled={!entry && !name.trim()}>
              {t('qualifications.save')}
            </Button>
          </Group>
        </Group>
      }
    >
      {!entry && (
        <Field label={t('qualifications.canDo.what')} hint={t('qualifications.canDo.whatHint')}>
          <Autocomplete
            value={name}
            onChange={setName}
            maxLength={120}
            placeholder={t('qualifications.canDo.example')}
            data={(kinds.data ?? []).filter((k) => k.selfService).map((k) => k.name)}
            data-autofocus
          />
        </Field>
      )}
      <Field label={t('qualifications.note')} hint={t('qualifications.canDo.noteHint')}>
        <Textarea autosize minRows={2} maxLength={500} value={note} onChange={(e) => setNote(e.currentTarget.value)} />
      </Field>
    </Modal>
  )
}
