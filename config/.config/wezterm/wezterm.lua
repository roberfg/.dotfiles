local wezterm = require 'wezterm'
local config = wezterm.config_builder()

if wezterm.target_triple:match('windows') then
    config.default_prog = { 'pwsh.exe' }
    config.initial_cols = 130
    config.initial_rows = 35

    wezterm.on('gui-startup', function(cmd)
        local _, _, mux_window = wezterm.mux.spawn_window(cmd or {})
        local gui_window = mux_window:gui_window()
        local screen = wezterm.gui.screens().active
        local dimensions = gui_window:get_dimensions()

        gui_window:set_position(
            screen.x + math.floor((screen.width - dimensions.pixel_width) / 2),
            screen.y + math.floor((screen.height - dimensions.pixel_height) / 2)
        )

        return mux_window
    end)
else
    config.default_prog = { 'bash', '-l' }
end

config.font_size = 11
config.color_scheme = 'OneDark (base16)'

return config
