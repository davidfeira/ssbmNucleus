using mexLib;
using mexLib.Types;
using mexLib.Utilties;

namespace MexCLI.Commands
{
    internal static class FighterAudioHelpers
    {
        public static int ResolveCssSfxId(MexWorkspace workspace, int announcerCall)
        {
            if (announcerCall == 540000)
                return -1;

            int bankIndex = announcerCall / 10000;
            int scriptIndex = announcerCall % 10000;
            if (bankIndex < 0 || bankIndex >= workspace.Project.SoundGroups.Count)
                return -1;

            var scripts = workspace.Project.SoundGroups[bankIndex].Scripts;
            if (scripts == null || scriptIndex < 0 || scriptIndex >= scripts.Count)
                return -1;

            int soundStartIndex = GetSoundStartIndex(workspace, bankIndex);
            if (soundStartIndex < 0)
                return -1;

            return GetOrCreateCssAnnouncerScript(
                workspace,
                announcerCall,
                scripts[scriptIndex],
                soundStartIndex);
        }

        public static int ApplyAnnouncerCallToCssIcons(
            MexWorkspace workspace,
            MexFighter fighter,
            int? externalId = null)
        {
            int cssSfxId = ResolveCssSfxId(workspace, fighter.AnnouncerCall);
            if (cssSfxId < 0)
                return -1;

            int iconExternalId = externalId ?? GetExternalId(workspace, fighter);
            if (iconExternalId < 0)
                return -1;

            foreach (MexCharacterSelectIcon icon in workspace.Project.CharacterSelect.FighterIcons)
            {
                if (icon.Fighter == iconExternalId)
                    icon.SFXID = cssSfxId;
            }

            return cssSfxId;
        }

        private static int GetExternalId(MexWorkspace workspace, MexFighter fighter)
        {
            int internalId = workspace.Project.Fighters.IndexOf(fighter);
            if (internalId < 0)
                return -1;
            return MexFighterIDConverter.ToExternalID(internalId, workspace.Project.Fighters.Count);
        }

        private static int GetSoundStartIndex(MexWorkspace workspace, int bankIndex)
        {
            int soundStartIndex = 0;
            for (int i = 0; i < bankIndex; i++)
                soundStartIndex += workspace.Project.SoundGroups[i].Sounds?.Count ?? 0;
            return soundStartIndex;
        }

        private static int GetOrCreateCssAnnouncerScript(
            MexWorkspace workspace,
            int announcerCall,
            SemScript sourceScript,
            int sourceSoundStartIndex)
        {
            MexSoundGroup cssGroup = workspace.Project.SoundGroups[0];
            if (cssGroup.Scripts == null)
                return -1;

            string cssScriptName = $"CSS announcer {announcerCall}";
            for (int i = 0; i < cssGroup.Scripts.Count; i++)
            {
                if (string.Equals(cssGroup.Scripts[i].Name, cssScriptName, StringComparison.Ordinal))
                    return i;
            }

            SemScript cssScript = new(sourceScript)
            {
                Name = cssScriptName,
            };

            foreach (SemCommand command in cssScript.Script)
            {
                if (command.SemCode == SemCode.Sound)
                    command.Value += sourceSoundStartIndex;
            }

            if (cssScript.GetFirstSoundID() < 0)
                return -1;

            cssGroup.Scripts.Add(cssScript);
            return cssGroup.Scripts.Count - 1;
        }
    }
}
