local wezterm = require 'wezterm'
local config = wezterm.config_builder()

if wezterm.target_os == 'windows' then
    config.default_prog = { 'pwsh.exe' }
else
    config.default_prog = { 'bash', '-l' }
end

config.font_size = 12

wezterm.apply_config_to_all_screens(config)
wezterm.apply_config(config)
