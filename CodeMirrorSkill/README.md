# CodeMirrorSkill

This provides a *SKILL* mode for CodeMirror editor.
The `skill` module adds a MIME type `x-skill` and a mode `skill` that can then be used with CodeMirror.

# Usage
* Clone this repository under `~/.ipython/profile_default/static/cmMode` (or equivalent).
* Then, add this line to `~/.ipython/profile_default/static/custom/custom.js`
  
  `require(["cmMode/skill/skill"], function() {console.log("SKILL mode loaded");})`
