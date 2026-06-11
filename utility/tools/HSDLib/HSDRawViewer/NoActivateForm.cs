using System.Windows.Forms;

namespace HSDRawViewer
{
    /// <summary>
    /// A Form that never steals keyboard focus / foreground activation.
    ///
    /// Used by the headless CLI render host (CSP generation batches spawn one
    /// process per render - a plain Form.Show() activates the window and
    /// yanks focus from whatever the user is typing in) and by the embedded
    /// viewer window. Mouse input still works normally; the window simply
    /// never becomes the foreground window.
    /// </summary>
    public class NoActivateForm : Form
    {
        private const int WS_EX_NOACTIVATE = 0x08000000;

        protected override bool ShowWithoutActivation => true;

        protected override CreateParams CreateParams
        {
            get
            {
                var cp = base.CreateParams;
                cp.ExStyle |= WS_EX_NOACTIVATE;
                return cp;
            }
        }
    }
}
