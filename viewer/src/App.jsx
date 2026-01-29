import { useState, useEffect } from 'react'
import StorageViewer from './components/StorageViewer'
import MexPanel from './components/MexPanel'
import Settings from './components/Settings'
import FirstRunSetup from './components/FirstRunSetup'
import SlippiSafetyDialog from './components/shared/SlippiSafetyDialog'
import DownloadModal from './components/shared/DownloadModal'
import { useDownloadQueue, DOWNLOAD_PHASES } from './hooks/useDownloadQueue'
import { playSound, playHoverSound } from './utils/sounds'
import './App.css'

const API_URL = 'http://127.0.0.1:5000/api/mex'

function App() {
  const [activeTab, setActiveTab] = useState('storage');
  const [metadata, setMetadata] = useState(null);
  const [loading, setLoading] = useState(true);
  const [skinCreatorOpen, setSkinCreatorOpen] = useState(false);

  // First-run setup state
  const [setupNeeded, setSetupNeeded] = useState(null); // null = checking, true = needed, false = complete

  // Download queue for nucleus:// imports
  const {
    currentDownload,
    phase,
    error,
    result,
    queueLength,
    queueDownload,
    clearDownload,
    proceedToNext,
    retryWithSlippiAction,
    retryWithDuplicateAction
  } = useDownloadQueue()

  // Check if first-run setup is needed
  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const response = await fetch(`${API_URL}/setup/status`);
        const data = await response.json();
        if (data.success) {
          setSetupNeeded(!data.complete);
        } else {
          // On error, assume setup is not needed to avoid blocking the app
          console.error('Failed to check setup status:', data.error);
          setSetupNeeded(false);
        }
      } catch (err) {
        console.error('Failed to check setup status:', err);
        // On network error, assume setup is not needed
        setSetupNeeded(false);
      }
    };
    checkSetupStatus();
  }, []);

  // Slippi dialog state for nucleus:// imports (legacy - keeping for other import paths)
  const [showSlippiDialog, setShowSlippiDialog] = useState(false);
  const [slippiDialogData, setSlippiDialogData] = useState(null);
  const [pendingImportData, setPendingImportData] = useState(null); // Stores {blob, name} for retry

  useEffect(() => {
    // Don't fetch metadata until setup is complete
    if (setupNeeded === false) {
      fetchMetadata();
    }

    // Listen for nucleus:// protocol imports
    if (window.electron?.onNucleusImport) {
      const cleanup = window.electron.onNucleusImport((data) => {
        console.log('[Nucleus] Import triggered:', data);
        const { url, name, title } = data;

        // Queue the download - the hook handles everything
        queueDownload({ url, name, title });
      });

      // Cleanup listener on unmount
      return cleanup;
    }
  }, [setupNeeded, queueDownload]);

  // Handle download completion - refresh metadata and play sound
  useEffect(() => {
    if (phase === DOWNLOAD_PHASES.COMPLETE && result?.success) {
      playSound('newSkin')
      fetchMetadata()
      setActiveTab('storage')
    }
  }, [phase, result]);

  const fetchMetadata = async () => {
    try {
      const response = await fetch(`${API_URL}/storage/metadata`);
      const data = await response.json();
      if (data.success) {
        setMetadata(data.metadata);
      }
    } catch (err) {
      console.error('Failed to fetch metadata:', err);
      setMetadata({ characters: {} });
    } finally {
      setLoading(false);
    }
  };

  // Handle slippi safety choice for nucleus imports
  const handleSlippiChoice = async (choice) => {
    setShowSlippiDialog(false);

    if (choice === 'cancel') {
      setPendingImportData(null);
      setSlippiDialogData(null);
      return;
    }

    if (!pendingImportData) {
      console.error('[Nucleus] No pending import data');
      return;
    }

    try {
      // Retry import with slippi_action
      const formData = new FormData();
      formData.append('file', pendingImportData.blob, `${pendingImportData.name || 'mod'}.zip`);
      formData.append('slippi_action', choice); // 'fix' or 'import_as_is'

      // Add custom title if provided
      if (pendingImportData.title) {
        formData.append('custom_title', pendingImportData.title);
      }

      const importResponse = await fetch(`${API_URL}/import/file`, {
        method: 'POST',
        body: formData
      });

      const result = await importResponse.json();

      if (result.success) {
        console.log('[Nucleus] Import successful after slippi choice:', result);
        fetchMetadata();
        setActiveTab('storage');
        alert(`Successfully imported: ${pendingImportData.name || 'mod'}`);
      } else {
        console.error('[Nucleus] Import failed after slippi choice:', result);
        alert(`Import failed: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('[Nucleus] Error during slippi retry:', error);
      alert(`Import failed: ${error.message}`);
    } finally {
      setPendingImportData(null);
      setSlippiDialogData(null);
    }
  };


  // Handle setup completion
  const handleSetupComplete = () => {
    setSetupNeeded(false);
    fetchMetadata();
  };

  // Handle slippi choice from download modal
  const handleDownloadSlippiChoice = async (choice) => {
    try {
      await retryWithSlippiAction(choice)
      // Success - effect will handle refresh and sound
    } catch (err) {
      // Error state is already set by the hook
      console.error('[Nucleus] Slippi retry failed:', err)
    }
  };

  // Handle duplicate choice from download modal
  const handleDownloadDuplicateChoice = async (choice) => {
    try {
      await retryWithDuplicateAction(choice)
      // Success - effect will handle refresh and sound
    } catch (err) {
      // Error state is already set by the hook
      console.error('[Nucleus] Duplicate retry failed:', err)
    }
  };

  // Handle download modal close
  const handleDownloadClose = () => {
    clearDownload()
  };

  // Show loading state while checking setup status
  if (setupNeeded === null) {
    return (
      <div className="app" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center', color: 'var(--color-text-secondary)' }}>
          <div className="setup-spinner" style={{
            width: '48px',
            height: '48px',
            border: '3px solid var(--color-border)',
            borderTopColor: 'var(--color-cyan)',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          Loading...
        </div>
      </div>
    );
  }

  // Show first-run setup if needed
  if (setupNeeded) {
    return <FirstRunSetup onComplete={handleSetupComplete} />;
  }

  return (
    <div className="app">
      {!skinCreatorOpen && (
        <header className="app-header">
          <div className="header-brand">
            <img src="./nucleuslogo.png" alt="SSBM Nucleus" className="header-logo" />
            <h1>SSBM Nucleus</h1>
          </div>
          <nav className="app-tabs">
            <button
              className={`tab ${activeTab === 'storage' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (activeTab !== 'storage') { playSound('boop'); setActiveTab('storage'); } }}
            >
              Vault
            </button>
            <button
              className={`tab ${activeTab === 'mex' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (activeTab !== 'mex') { playSound('boop'); setActiveTab('mex'); } }}
            >
              Install
            </button>
            <button
              className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
              onMouseEnter={playHoverSound}
              onClick={() => { if (activeTab !== 'settings') { playSound('boop'); setActiveTab('settings'); } }}
            >
              Settings
            </button>
          </nav>
        </header>
      )}

      <main className="app-content">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '48px', color: '#888' }}>
            Loading...
          </div>
        ) : (
          <>
            <div style={{ display: activeTab === 'storage' ? 'block' : 'none' }}>
              <StorageViewer metadata={metadata} onRefresh={fetchMetadata} onSkinCreatorChange={setSkinCreatorOpen} />
            </div>
            <div style={{ display: activeTab === 'mex' ? 'block' : 'none', height: '100%' }}>
              <MexPanel />
            </div>
            <div style={{ display: activeTab === 'settings' ? 'block' : 'none' }}>
              <Settings metadata={metadata} />
            </div>
          </>
        )}
      </main>

      {/* Slippi safety dialog for nucleus:// imports (legacy) */}
      <SlippiSafetyDialog
        show={showSlippiDialog}
        data={slippiDialogData}
        onChoice={handleSlippiChoice}
      />

      {/* Download modal for nucleus:// protocol imports */}
      <DownloadModal
        download={currentDownload}
        phase={phase}
        error={error}
        result={result}
        queueLength={queueLength}
        onClose={handleDownloadClose}
        onProceedToNext={proceedToNext}
        onSlippiChoice={handleDownloadSlippiChoice}
        onDuplicateChoice={handleDownloadDuplicateChoice}
      />
    </div>
  )
}

export default App
