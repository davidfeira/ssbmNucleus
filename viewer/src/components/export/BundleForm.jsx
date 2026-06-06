import React from 'react';

/**
 * Bundle (.ssbm) creation form. A bundle = the ISO's xdelta patch + the texture
 * pack + a cover image, so it's only offered when a texture pack was applied
 * (without textures it would just be a patch).
 */
const BundleForm = ({
  bundleName,
  setBundleName,
  bundleDescription,
  setBundleDescription,
  bundleImagePreview,
  onImageChange,
  onRemoveImage,
  onSubmit,
  onCancel,
  vanillaMissing,
}) => (
  <div className="bundle-form">
    <h3>Export as Bundle</h3>
    <p className="bundle-form-intro">
      Create a shareable <code>.ssbm</code> file (patch + texture pack) that friends
      can install with one click.
    </p>

    {vanillaMissing && (
      <div className="auto-warning-box">
        <p>
          Set your <strong>vanilla ISO path</strong> in Settings first — it’s needed to
          build the patch inside the bundle.
        </p>
      </div>
    )}

    <div className="form-field">
      <label>Bundle Name</label>
      <input
        type="text"
        value={bundleName}
        onChange={(e) => setBundleName(e.target.value)}
        placeholder="My Awesome Mod Pack"
      />
    </div>

    <div className="form-field">
      <label>Description (optional)</label>
      <textarea
        value={bundleDescription}
        onChange={(e) => setBundleDescription(e.target.value)}
        placeholder="Describe what's in this bundle..."
        rows={2}
      />
    </div>

    <div className="form-field">
      <label>Cover Image (optional)</label>
      <div className="image-input-row">
        {bundleImagePreview ? (
          <div className="image-preview">
            <img src={bundleImagePreview} alt="Bundle preview" />
            <button className="remove-image" onClick={onRemoveImage}>✕</button>
          </div>
        ) : (
          <label className="image-select-btn">
            <input
              type="file"
              accept="image/*"
              onChange={onImageChange}
              style={{ display: 'none' }}
            />
            Select Image
          </label>
        )}
      </div>
    </div>

    <div className="form-actions">
      <button
        className="btn-export"
        onClick={onSubmit}
        disabled={!bundleName.trim() || vanillaMissing}
        style={{ background: 'var(--gradient-gold)' }}
      >
        Create Bundle
      </button>
      <button className="btn-secondary" onClick={onCancel}>Cancel</button>
    </div>
  </div>
);

export default BundleForm;
