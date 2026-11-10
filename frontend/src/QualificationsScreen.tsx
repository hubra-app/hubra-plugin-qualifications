import { useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Badge, Button, Group, Modal, NumberInput, Paper, Select, Stack, Switch, Text, TextInput, Textarea } from '@mantine/core'
import { IconCertificate, IconPencil, IconPlus } from '@tabler/icons-react'
import {
  ConfirmModal,
  EmptyState,
  ErrorBanner,
  LoadingSpinner,
  MemberPicker,
  PageHead,
  Seg,
  formatDate,
  useT,
  useToast,
} from '@hubra/plugin-sdk'
import {
  addQualification,
  createKind,
  deleteKind,
  deleteQualification,
  listKinds,
  listQualifications,
  updateKind,
  updateQualification,
  type KindInput,
  type Qualification,
  type QualificationKind,
  type QualificationState,
} from './api'

export const STATE_COLOR: Record<QualificationState, string> = { valid: 'green', soon: 'yellow', expired: 'red' }
const KINDS = ['qualifications', 'kinds']
const LIST = ['qualifications', 'qualifications']
const today = () => new Date().toISOString().slice(0, 10)

function useRun() {
  const { notify } = useToast()
  return async (fn: () => Promise<unknown>) => {
    try {
      await fn()
      return true
    } catch (err) {
      notify('error', err instanceof Error ? err.message : String(err))
      return false
    }
  }
}

/** Who holds which qualification and until when; the soonest expiry first. */
export function QualificationsScreen() {
  const { t } = useT()
  const kinds = useQuery({ queryKey: KINDS, queryFn: listKinds })
  const list = useQuery({ queryKey: LIST, queryFn: listQualifications })
  const [filter, setFilter] = useState<'all' | QualificationState>('all')
  const [kindFilter, setKindFilter] = useState<string | null>(null)
  const [editing, setEditing] = useState<Qualification | 'new' | null>(null)
  const [editKind, setEditKind] = useState<QualificationKind | 'new' | null>(null)

  const rows = useMemo(
    () =>
      (list.data ?? []).filter(
        (q) => (filter === 'all' || q.state === filter) && (!kindFilter || String(q.kindId) === kindFilter),
      ),
    [list.data, filter, kindFilter],
  )
  if (list.error) return <ErrorBanner message={(list.error as Error).message} onRetry={() => list.refetch()} />
  if (list.isLoading || kinds.isLoading) return <LoadingSpinner />
  const count = (s: QualificationState) => (list.data ?? []).filter((q) => q.state === s).length

  return (
    <>
      <PageHead
        title={t('qualifications.title')}
        desc={t('qualifications.desc')}
        actions={
          <Group gap="xs">
            <Button variant="default" onClick={() => setEditKind('new')}>
              {t('qualifications.addKind')}
            </Button>
            <Button leftSection={<IconPlus size={16} />} onClick={() => setEditing('new')} disabled={!kinds.data?.length}>
              {t('qualifications.add')}
            </Button>
          </Group>
        }
      />

      {!!kinds.data?.length && (
        <Group gap={6} mb="md">
          {kinds.data.map((k) => (
            <Badge
              key={k.id}
              variant="outline"
              color="gray"
              size="lg"
              style={{ textTransform: 'none', cursor: 'pointer' }}
              rightSection={<IconPencil size={12} />}
              onClick={() => setEditKind(k)}
            >
              {k.name}
              {k.selfService ? ` · ${t('qualifications.selfServiceShort')}` : ''}
              {k.validMonths ? ` · ${t('qualifications.months', { count: k.validMonths })}` : ''}
            </Badge>
          ))}
        </Group>
      )}

      <Group mb="md" gap="sm" wrap="wrap">
        <Seg
          value={filter}
          onChange={(v: string) => setFilter(v as typeof filter)}
          options={[
            { value: 'all', label: t('qualifications.all') },
            { value: 'soon', label: `${t('qualifications.state.soon')} (${count('soon')})` },
            { value: 'expired', label: `${t('qualifications.state.expired')} (${count('expired')})` },
          ]}
        />
        <Select
          w={220}
          clearable
          placeholder={t('qualifications.allKinds')}
          value={kindFilter}
          onChange={setKindFilter}
          data={(kinds.data ?? []).map((k) => ({ value: String(k.id), label: k.name }))}
        />
      </Group>

      {!rows.length ? (
        <EmptyState
          icon={<IconCertificate size={28} />}
          title={t('qualifications.none')}
          description={kinds.data?.length ? t('qualifications.noneHint') : t('qualifications.noKinds')}
        />
      ) : (
        <Paper withBorder radius="md">
          {rows.map((q) => (
            <Group
              key={q.id}
              justify="space-between"
              wrap="nowrap"
              px="md"
              py="sm"
              style={{ borderBottom: '1px solid var(--mantine-color-gray-2)', cursor: 'pointer' }}
              onClick={() => setEditing(q)}
            >
              <div style={{ minWidth: 0 }}>
                <Text fw={600} fz="sm" truncate>
                  {q.memberName}
                </Text>
                <Text fz="xs" c="dimmed">
                  {q.kindName} · {t('qualifications.since', { date: formatDate(q.obtainedOn) })}
                  {q.note ? ` · ${q.note}` : ''}
                </Text>
              </div>
              <Group gap="sm" wrap="nowrap">
                <Text fz="sm" c={q.state === 'valid' ? 'dimmed' : undefined} className="num">
                  {q.expiresOn ? formatDate(q.expiresOn) : '–'}
                </Text>
                <Badge variant="light" color={STATE_COLOR[q.state]} style={{ textTransform: 'none' }}>
                  {t(`qualifications.state.${q.state}`)}
                </Badge>
              </Group>
            </Group>
          ))}
        </Paper>
      )}

      {editing && <QualificationForm entry={editing === 'new' ? null : editing} kinds={kinds.data ?? []} onClose={() => setEditing(null)} />}
      {editKind && <KindForm kind={editKind === 'new' ? null : editKind} onClose={() => setEditKind(null)} />}
    </>
  )
}

function QualificationForm({ entry, kinds, onClose }: { entry: Qualification | null; kinds: QualificationKind[]; onClose: () => void }) {
  const { t } = useT()
  const qc = useQueryClient()
  const run = useRun()
  const [memberId, setMemberId] = useState<string | null>(entry ? String(entry.memberId) : null)
  const [kindId, setKindId] = useState<string | null>(entry ? String(entry.kindId) : kinds.length === 1 ? String(kinds[0].id) : null)
  const [obtainedOn, setObtainedOn] = useState(entry?.obtainedOn ?? today())
  // Empty: from the qualification's validity.
  const [expiresOn, setExpiresOn] = useState(entry?.expiresOn ?? '')
  const [note, setNote] = useState(entry?.note ?? '')
  const [busy, setBusy] = useState(false)
  const [asking, setAsking] = useState(false)
  const kind = kinds.find((k) => String(k.id) === kindId)

  const save = async () => {
    setBusy(true)
    const body = { obtainedOn, note: note.trim() || null, ...(expiresOn ? { expiresOn } : {}) }
    const ok = await run(() =>
      entry
        ? updateQualification(entry.id, { ...body, expiresOn: expiresOn || null })
        : addQualification({ ...body, memberId: Number(memberId), kindId: Number(kindId) }),
    )
    setBusy(false)
    if (ok) {
      qc.invalidateQueries({ queryKey: ['qualifications'] })
      onClose()
    }
  }
  const remove = async () => {
    if (entry && (await run(() => deleteQualification(entry.id)))) {
      qc.invalidateQueries({ queryKey: ['qualifications'] })
      onClose()
    }
  }

  return (
    <Modal opened onClose={onClose} title={entry ? `${entry.memberName}: ${entry.kindName}` : t('qualifications.add')}>
      <Stack gap="sm">
        {!entry && (
          <>
            <MemberPicker label={t('qualifications.member')} value={memberId} onChange={(id) => setMemberId(id)} required />
            <Select label={t('qualifications.kind')} data={kinds.map((k) => ({ value: String(k.id), label: k.name }))} value={kindId} onChange={setKindId} required />
          </>
        )}
        <TextInput type="date" label={t('qualifications.obtainedOn')} value={obtainedOn} max={today()} onChange={(e) => setObtainedOn(e.currentTarget.value)} required />
        <TextInput
          type="date"
          label={t('qualifications.expiresOn')}
          description={
            kind?.validMonths || entry
              ? t('qualifications.expiresHint')
              : t('qualifications.noExpiryHint')
          }
          value={expiresOn}
          min={obtainedOn}
          onChange={(e) => setExpiresOn(e.currentTarget.value)}
        />
        <TextInput label={t('qualifications.note')} placeholder={t('qualifications.notePlaceholder')} value={note} maxLength={500} onChange={(e) => setNote(e.currentTarget.value)} />
        <Group justify="space-between" mt="sm">
          {entry ? (
            <Button variant="subtle" color="red" onClick={() => setAsking(true)}>
              {t('qualifications.remove')}
            </Button>
          ) : (
            <span />
          )}
          <Button onClick={save} loading={busy} disabled={!obtainedOn || (!entry && (!memberId || !kindId))}>
            {entry ? t('qualifications.save') : t('qualifications.add')}
          </Button>
        </Group>
      </Stack>
      <ConfirmModal open={asking} onClose={() => setAsking(false)} onConfirm={remove} title={t('qualifications.remove')} body={t('qualifications.removeConfirm')} confirmLabel={t('qualifications.remove')} />
    </Modal>
  )
}

function KindForm({ kind, onClose }: { kind: QualificationKind | null; onClose: () => void }) {
  const { t } = useT()
  const qc = useQueryClient()
  const run = useRun()
  const [form, setForm] = useState<KindInput>({
    name: kind?.name ?? '',
    description: kind?.description ?? null,
    validMonths: kind?.validMonths ?? null,
    remindDays: kind?.remindDays ?? 30,
    selfService: kind?.selfService ?? false,
  })
  const [busy, setBusy] = useState(false)
  const [asking, setAsking] = useState(false)

  const save = async () => {
    setBusy(true)
    const ok = await run(() => (kind ? updateKind(kind.id, form) : createKind(form)))
    setBusy(false)
    if (ok) {
      qc.invalidateQueries({ queryKey: ['qualifications'] })
      onClose()
    }
  }
  const remove = async () => {
    if (kind && (await run(() => deleteKind(kind.id)))) {
      qc.invalidateQueries({ queryKey: ['qualifications'] })
      onClose()
    }
  }

  return (
    <Modal opened onClose={onClose} title={kind ? kind.name : t('qualifications.addKind')}>
      <Stack gap="sm">
        <TextInput label={t('qualifications.kindName')} placeholder={t('qualifications.kindPlaceholder')} value={form.name} maxLength={120} onChange={(e) => setForm({ ...form, name: e.currentTarget.value })} required />
        <Textarea label={t('qualifications.description')} autosize minRows={2} value={form.description ?? ''} onChange={(e) => setForm({ ...form, description: e.currentTarget.value || null })} />
        <NumberInput
          label={t('qualifications.validMonths')}
          description={t('qualifications.validMonthsHint')}
          min={1}
          max={600}
          allowDecimal={false}
          value={form.validMonths ?? ''}
          onChange={(v) => setForm({ ...form, validMonths: typeof v === 'number' ? v : null })}
        />
        <NumberInput
          label={t('qualifications.remindDays')}
          description={t('qualifications.remindDaysHint')}
          min={0}
          max={365}
          allowDecimal={false}
          value={form.remindDays}
          onChange={(v) => setForm({ ...form, remindDays: typeof v === 'number' ? v : 30 })}
        />
        <Switch
          label={t('qualifications.selfService')}
          description={t('qualifications.selfServiceHint')}
          checked={form.selfService}
          onChange={(e) => setForm({ ...form, selfService: e.currentTarget.checked })}
        />
        <Group justify="space-between" mt="sm">
          {kind ? (
            <Button variant="subtle" color="red" onClick={() => setAsking(true)}>
              {t('qualifications.deleteKind')}
            </Button>
          ) : (
            <span />
          )}
          <Button onClick={save} loading={busy} disabled={!form.name.trim()}>
            {t('qualifications.save')}
          </Button>
        </Group>
      </Stack>
      <ConfirmModal open={asking} onClose={() => setAsking(false)} onConfirm={remove} title={t('qualifications.deleteKind')} body={t('qualifications.deleteKindConfirm', { name: kind?.name ?? '' })} confirmLabel={t('qualifications.deleteKind')} />
    </Modal>
  )
}
