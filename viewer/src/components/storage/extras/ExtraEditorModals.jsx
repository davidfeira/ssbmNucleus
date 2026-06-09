import LaserEditorModal from '../LaserEditorModal'
import SideBEditorModal from '../SideBEditorModal'
import UpBEditorModal from '../UpBEditorModal'
import ShineEditorModal from '../ShineEditorModal'
import SwordEditorModal from '../SwordEditorModal'
import LaserRingEditorModal from '../LaserRingEditorModal'
import DualColorEditorModal from '../DualColorEditorModal'
import GunEditorModal from '../GunEditorModal'

/**
 * ExtraEditorModals - Renders the appropriate editor modal for the
 * currently selected extra type. `editor` groups the modal state and
 * handlers from useExtrasManager.
 */
export default function ExtraEditorModals({ selectedType, character, API_URL, editor }) {
  const { show, editingMod, onClose, onSave, onDelete } = editor

  return (
    <>
      {/* Laser Editor Modal */}
      {selectedType.id === 'laser' && (
        <LaserEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Side-B Editor Modal */}
      {selectedType.id === 'sideb' && (
        <SideBEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Up-B Editor Modal */}
      {selectedType.id === 'upb' && (
        <UpBEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Shine Editor Modal */}
      {selectedType.id === 'shine' && (
        <ShineEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Laser Ring Editor Modal */}
      {selectedType.id === 'laser_ring' && (
        <LaserRingEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Sword Editor Modal */}
      {selectedType.id === 'sword' && (
        <SwordEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Dual Color Editor Modal - for punch, thunder, fireball, shadow ball effects */}
      {['falcon_punch', 'warlock_punch', 'thunder', 'pk_thunder', 'fireball', 'shadow_ball'].includes(selectedType.id) && (
        <DualColorEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}

      {/* Gun Editor Modal - for model type extras */}
      {selectedType.type === 'model' && (
        <GunEditorModal
          show={show}
          character={character}
          extraType={selectedType}
          editingMod={editingMod}
          onClose={onClose}
          onSave={onSave}
          onDelete={onDelete}
          API_URL={API_URL}
        />
      )}
    </>
  )
}
