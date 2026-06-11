import './Settings.css'
import { API_URL } from '../config'
import BackupRestore from './settings/BackupRestore'
import StorageStatsSection from './settings/StorageStatsSection'
import AdditionalDataSection from './settings/AdditionalDataSection'
import IsoPathSection from './settings/IsoPathSection'
import SlippiPathSection from './settings/SlippiPathSection'
import HdCspSection from './settings/HdCspSection'
import ClearStorageSection from './settings/ClearStorageSection'
import DiscordSection from './settings/DiscordSection'
import VolumeSection from './settings/VolumeSection'
import SetupSection from './settings/SetupSection'
import AiStudioSection from './settings/AiStudioSection'

export default function Settings({ metadata, onOpenFirstRunSetup }) {

  return (
    <div className="settings-container">
      <div className="settings-content">
        <h2>Settings</h2>

        {/* Card grid - sections flow into as many columns as fit the window */}
        <div className="settings-grid">
          {/* Paths & setup */}
          <IsoPathSection API_URL={API_URL} />
          <SlippiPathSection API_URL={API_URL} />
          <AiStudioSection API_URL={API_URL} />
          <SetupSection onOpenFirstRunSetup={onOpenFirstRunSetup} />

          {/* App + community */}
          <VolumeSection />
          <DiscordSection />

          {/* Vault tools */}
          <HdCspSection metadata={metadata} API_URL={API_URL} />
          <BackupRestore API_URL={API_URL} />
          <AdditionalDataSection />

          {/* Data */}
          <StorageStatsSection metadata={metadata} />
          <ClearStorageSection metadata={metadata} API_URL={API_URL} />
        </div>
      </div>
    </div>
  )
}
