# Open Questions

This page tracks the parts of the current Melee and Nucleus workflow that still need clean documentation.

## High-Value Gaps

- how stage archives are structured and how Nucleus detects them
- what the DAS workflow expects from an imported stage set
- which effect edits are Slippi-safe, unsafe, or situational
- how CSP generation, alt CSPs, and pose capture are organized end to end
- how texture-pack export mode works and what assumptions it makes

## Knowledge That Exists Mostly In Code

- dynamic offset detection for several Fox and Falco effect types
- stage import, rename, reorder, and variant handling
- costume validation and Slippi override flows
- gun model and up-B texture editing paths
- some Ice Climbers-specific scene and pairing assumptions, especially around composite CSP generation

## Standard For Closing A Gap

A topic should count as documented only when there is a short page that explains:

1. what the asset or system is
2. where the relevant data lives
3. what is known vs inferred
4. what tools or workflows are used to test it

Raw notes alone are useful, but they should not be the final resting place for important knowledge.
