import { useState } from 'react'
import { ActionIcon, Badge, Button, Group, Paper, Text } from '@mantine/core'
import { useQuery } from '@tanstack/react-query'
import { IconCertificate, IconPencil, IconPlus } from '@tabler/icons-react'
import { formatDate, useT } from '@hubra/plugin-sdk'
import { myQualifications, type Qualification } from './api'
import { CanDoModal } from './CanDoScreen'
import { STATE_COLOR } from './QualificationsScreen'

/** The member's own qualifications and until when they hold, and what they
 *  can do (self-service ones), which they add and change here. */
export function MyQualificationsCard() {
  const { t } = useT()
  const { data = [] } = useQuery({ queryKey: ['qualifications', 'qualifications', 'mine'], queryFn: myQualifications })
  const [editing, setEditing] = useState<Qualification | 'new' | null>(null)
  return (
    <Paper withBorder shadow="sm" radius="lg">
      <Group p="md" gap="sm" justify="space-between" style={{ borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
        <Group gap="sm">
          <IconCertificate size={16} style={{ color: '#6b7480' }} />
          <Text fw={700} fz="md">
            {t('qualifications.mine')}
          </Text>
        </Group>
        <Button size="xs" variant="subtle" leftSection={<IconPlus size={14} />} onClick={() => setEditing('new')}>
          {t('qualifications.canDo.add')}
        </Button>
      </Group>
      {data.length === 0 && (
        <Text px="md" py="sm" fz="sm" c="dimmed">
          {t('qualifications.canDo.noneMine')}
        </Text>
      )}
      {data.map((q) => (
        <Group key={q.id} justify="space-between" px="md" py="sm" wrap="nowrap" style={{ borderBottom: '1px solid var(--mantine-color-gray-2)' }}>
          <div style={{ minWidth: 0 }}>
            <Text fw={600} fz="sm">
              {q.kindName}
            </Text>
            <Text fz="xs" c="dimmed" truncate>
              {q.selfService
                ? [q.note || t('qualifications.canDo.selfAdded'), q.confirmedBy && t('qualifications.canDo.confirmedBy', { name: q.confirmedBy })]
                    .filter(Boolean)
                    .join(' · ')
                : q.expiresOn
                  ? t('qualifications.until', { date: formatDate(q.expiresOn) })
                  : t('qualifications.noExpiry')}
            </Text>
          </div>
          {q.selfService ? (
            <ActionIcon variant="subtle" onClick={() => setEditing(q)} aria-label={t('qualifications.canDo.edit')}>
              <IconPencil size={16} />
            </ActionIcon>
          ) : (
            <Badge variant="light" color={STATE_COLOR[q.state]} style={{ textTransform: 'none', flexShrink: 0 }}>
              {t(`qualifications.state.${q.state}`)}
            </Badge>
          )}
        </Group>
      ))}
      {editing && <CanDoModal entry={editing === 'new' ? null : editing} onClose={() => setEditing(null)} />}
    </Paper>
  )
}
