# Menus And Select Screen Mods

Menu mods change the game's select screens and in-game HUD instead of characters or stages: the Character Select Screen (CSS), the Stage Select Screen (SSS), and the HUD textures shown during a match.

They live in the **Menus** area of the install side of the app, with their own vault sections under the hood.

## The Menu Mod Types

- **CSS icon grids** — replacement sets for the character icons on the CSS
- **Menu backgrounds** — the animated backdrop behind the CSS or SSS
- **CSS doors** — the port panels ("doors") on the CSS
- **Layouts** — where the icons actually sit on the CSS and SSS
- **In-Game HUD** — pause screen textures, the damage percent font, and the Ready / Go / Game graphics

## CSS Icon Grids

An icon-grid mod is a full or partial set of replacement character icons.

Imports accept two flavors:

- **loose PNGs** named after characters — a large alias table maps names like `falc.png`, `gnw.png`, `ics.png` to the right character
- **compiled CSS files** (`MnSlChr.dat`/`.usd`, `mexSelectChr.dat`) — Nucleus extracts the icons out of the file for you

Either way the mod is normalized into one labeled icon per character, so after import you can:

- relabel an icon to a different character
- replace, add, or delete individual icons
- install the whole grid into the open project, or just one icon at a time

## Menu Backgrounds

A background mod is a model/animation bundle extracted from a menu file, plus an optional preview screenshot.

The same background pool installs into **either** screen: pick a background and install it to the CSS, the SSS, or both.

## CSS Doors

A door mod is a single `door.png` texture for the CSS port panels. Import it, preview it, install it into the open project.

## Layout Editors

Both select screens have layout editors that read and write the open project directly:

- the **CSS layout** editor moves the character icons on the grid
- the **SSS layout** editor moves the stage icons

These need an open project, since the layout is project state rather than a vault item.

## In-Game HUD

The HUD tab covers match-time textures:

- **Pause Screen** — the texture set shown on the pause camera overlay
- **Percent Font** — the damage number glyphs
- **Ready / Go / Game** — the match start/end word graphics

These come as texture packs in the vault and install into the open project like other menu mods. Pause-screen mods can be previewed with a live in-game capture (see [Test In Game](Test-In-Game.md)).

## Importing Menu Mods

Menu mods go through the same floating Import button as everything else ([Manual Import](Manual-Import.md)) — a ZIP containing a CSS dat or icon set is detected and routed to the menus importer automatically.

## Vault Vs Project, Again

The usual split applies:

- importing, editing, and deleting menu mods works on the vault and needs no open project
- **installing** any menu mod writes into the open MEX project and requires one

## A Note On Patch Builds

Some patch builds (like Animelee) paint their own CSS/SSS over the scene. When you create a project from such a patch, Nucleus resets the menu scenes to vanilla first so installed menu mods and grids behave predictably.

## Related Pages

- [Vault Vs Project](Vault-Vs-Project.md)
- [Manual Import](Manual-Import.md)
- [Test In Game](Test-In-Game.md)
