import './Settings.css'
import BackupRestore from './settings/BackupRestore'
import StorageStatsSection from './settings/StorageStatsSection'
import IsoPathSection from './settings/IsoPathSection'
import SlippiPathSection from './settings/SlippiPathSection'
import HdCspSection from './settings/HdCspSection'
import ClearStorageSection from './settings/ClearStorageSection'

const API_URL = 'http://127.0.0.1:5000/api/mex'

export default function Settings({ metadata }) {

  return (
    <div className="settings-container">
      <div className="settings-content">
        <h2>Settings</h2>

        {/* Vanilla ISO Path */}
        <IsoPathSection API_URL={API_URL} />

        {/* Slippi Dolphin Path */}
        <SlippiPathSection API_URL={API_URL} />

        {/* Storage Statistics */}
        <StorageStatsSection metadata={metadata} />

        {/* Vault Backup & Restore Section */}
        <BackupRestore API_URL={API_URL} />

        {/* HD CSP Generation Section */}
        <HdCspSection metadata={metadata} API_URL={API_URL} />

        {/* Clear Storage Section */}
        <ClearStorageSection metadata={metadata} API_URL={API_URL} />
      </div>
    </div>
  )
}
