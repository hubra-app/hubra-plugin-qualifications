import { registerPlugin } from '@hubra/plugin-sdk'
import { IconCertificate, IconTools } from '@tabler/icons-react'
import { CanDoScreen } from './CanDoScreen'
import { MyQualificationsCard } from './MyQualificationsCard'
import { QualificationsScreen } from './QualificationsScreen'
import translations from './translations.json'

const MODULE = 'qualifications'
const MANAGE = 'qualifications.members.manage'

registerPlugin({
  id: 'qualifications',
  routes: [
    { path: 'skills', module: MODULE, component: CanDoScreen },
    { path: 'qualifications', module: MODULE, perm: MANAGE, component: QualificationsScreen },
    // Where the page was while it belonged to Guides.
    { path: 'inventory/qualifications', module: MODULE, perm: MANAGE, component: QualificationsScreen },
  ],
  slots: [{ slot: 'account.cards', module: MODULE, component: MyQualificationsCard }],
  // The nav entries in hubra_qualifications/__init__.py name these icons.
  icons: { certificate: IconCertificate, tools: IconTools },
  translations,
})
