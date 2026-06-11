/**
 * Inline styles for the Pose Manager modal (rendered via a <style> tag).
 */
export const POSE_MANAGER_STYLES = `
        .pm-overlay {
          position: absolute;
          inset: 0;
          background: rgba(0, 0, 0, 0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: calc(var(--z-modal) + 40);
          padding: var(--page-block-padding) var(--modal-inline-padding);
          overflow: auto;
          overscroll-behavior: contain;
        }

        .pm-modal {
          background: #1a1a2e;
          border-radius: 12px;
          width: min(100%, 68rem);
          height: min(100%, var(--modal-max-height));
          max-height: 100%;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
          margin: auto;
        }

        @media (min-width: 1440px) {
          .pm-modal {
            max-width: 1100px;
          }
        }

        @media (min-width: 1920px) {
          .pm-modal {
            max-width: 1250px;
          }
        }

        @media (min-width: 2560px) {
          .pm-modal {
            max-width: 1500px;
          }
        }

        .pm-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          background: #16162a;
          border-bottom: 1px solid #2a2a4a;
        }

        .pm-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .pm-title-label {
          font-size: 18px;
          font-weight: 600;
          color: #fff;
        }

        .pm-title-char {
          font-size: 14px;
          color: #888;
          padding: 4px 10px;
          background: #2a2a4a;
          border-radius: 4px;
        }

        .pm-close-btn {
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          padding: 8px;
          border-radius: 6px;
          transition: all 0.15s ease;
        }

        .pm-close-btn:hover {
          background: #2a2a4a;
          color: #fff;
        }

        .pm-body {
          flex: 1;
          display: flex;
          overflow: hidden;
          min-height: 0;
        }

        /* Left: Viewer + Category Section */
        .pm-left-section {
          display: flex;
          flex-direction: column;
          flex: 1;
          border-right: 1px solid #2a2a4a;
          min-width: 0;
        }

        .pm-viewer-section {
          flex: 1;
          position: relative;
          overflow: hidden;
          /* Never let the embedded native viewer collapse on short windows */
          min-height: clamp(180px, 38vh, 320px);
          min-width: 240px;
        }

        /* Category bar below viewer */
        .pm-category-bar {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          padding: 10px 12px;
          background: #16162a;
          border-top: 1px solid #2a2a4a;
        }

        .pm-cat-btn {
          padding: 5px 10px;
          background: #2a2a4a;
          border: none;
          border-radius: 4px;
          color: #888;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pm-cat-btn:hover {
          background: #3a3a5a;
          color: #ccc;
        }

        .pm-cat-btn.active {
          background: #4a9eff;
          color: #fff;
        }

        .pm-viewer-section .mv-overlay {
          position: absolute !important;
          inset: 0 !important;
          width: 100% !important;
          height: 100% !important;
          padding: 0 !important;
          overflow: hidden !important;
          background: transparent !important;
          backdrop-filter: none !important;
          z-index: 1 !important;
        }

        .pm-viewer-section .mv-container {
          width: 100% !important;
          height: 100% !important;
          max-width: none !important;
          max-height: none !important;
          border-radius: 0 !important;
          border: none !important;
          box-shadow: none !important;
          background:
            radial-gradient(ellipse at 50% 30%, rgba(125, 211, 232, 0.03) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(125, 211, 232, 0.02) 0%, transparent 40%),
            linear-gradient(180deg, #0d1929 0%, #0a1420 100%) !important;
        }

        .pm-viewer-section .mv-header {
          display: none !important;
        }

        .pm-viewer-section .mv-body {
          flex: 1 !important;
          min-height: 0 !important;
        }

        .pm-viewer-section .mv-viewport {
          flex: 1 !important;
          margin: 0 !important;
          border: none !important;
          border-radius: 0 !important;
          min-height: 0 !important;
          background: transparent !important;
        }

        .pm-viewer-section .mv-sidebar {
          display: none;
        }

        .pm-viewer-section .mv-controls {
          background: rgba(0, 0, 0, 0.5);
          border-top: 1px solid #2a2a4a;
        }

        /* Right: Poses Section */
        .pm-poses-section {
          width: 260px;
          min-width: 240px;
          display: flex;
          flex-direction: column;
          background: #16162a;
          min-height: 0;
        }

        .pm-poses-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid #2a2a4a;
          font-size: 14px;
          font-weight: 500;
          color: #fff;
        }

        .pm-poses-count {
          background: #2a2a4a;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 12px;
          color: #888;
        }

        .pm-poses-grid {
          flex: 1;
          overflow-y: auto;
          padding: 10px;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          align-content: start;
        }

        .pm-poses-loading,
        .pm-poses-empty {
          grid-column: 1 / -1;
          text-align: center;
          color: #666;
          font-size: 13px;
          padding: 40px 20px;
          line-height: 1.6;
        }

        /* Pose Card */
        .pm-pose-card {
          background: #1a1a2e;
          border: 1px solid #2a2a4a;
          border-radius: 8px;
          overflow: hidden;
          transition: all 0.15s ease;
        }

        .pm-pose-card:hover {
          border-color: #4a9eff;
          transform: translateY(-2px);
        }

        .pm-pose-image {
          position: relative;
          aspect-ratio: 3 / 4;
          background: #0d1929;
          overflow: hidden;
        }

        .pm-pose-image img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .pm-pose-placeholder {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
          font-weight: 600;
          color: #2a2a4a;
          background: linear-gradient(135deg, #1a1a2e 0%, #0d1929 100%);
        }

        .pm-pose-delete {
          position: absolute;
          top: 6px;
          right: 6px;
          background: rgba(220, 53, 69, 0.9);
          border: none;
          border-radius: 4px;
          padding: 6px;
          color: #fff;
          cursor: pointer;
          opacity: 0;
          transition: opacity 0.15s ease;
        }

        .pm-pose-card:hover .pm-pose-delete {
          opacity: 1;
        }

        .pm-pose-delete:hover {
          background: #dc3545;
        }

        .pm-pose-name {
          padding: 8px;
          font-size: 12px;
          color: #ccc;
          text-align: center;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .pm-save-controls {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
          background: #16162a;
          border-top: 1px solid #2a2a4a;
        }

        .pm-pose-name-input {
          flex: 1;
          padding: 12px 16px;
          background: #1a1a2e;
          border: 1px solid #2a2a4a;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          outline: none;
          transition: border-color 0.15s ease;
        }

        .pm-pose-name-input:focus {
          border-color: #4a9eff;
        }

        .pm-pose-name-input::placeholder {
          color: #666;
        }

        .pm-pose-name-input:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pm-save-btn {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: linear-gradient(135deg, #4a9eff, #3d7ede);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .pm-save-btn:hover:not(:disabled) {
          background: linear-gradient(135deg, #5aadff, #4d8eee);
          transform: translateY(-1px);
        }

        .pm-save-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .pm-message {
          padding: 12px 20px;
          font-size: 14px;
          text-align: center;
        }

        .pm-error {
          background: rgba(220, 53, 69, 0.2);
          color: #ff6b6b;
          border-top: 1px solid rgba(220, 53, 69, 0.3);
        }

        .pm-success {
          background: rgba(40, 167, 69, 0.2);
          color: #51cf66;
          border-top: 1px solid rgba(40, 167, 69, 0.3);
        }

        @media (max-width: 1024px) {
          .pm-modal {
            width: 100%;
          }
        }
      `
