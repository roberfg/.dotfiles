local wezterm = require 'wezterm'
local config = wezterm.config_builder()

local triple = wezterm.target_triple

if triple:match('windows') then
    config.default_prog = { 'pwsh.exe' }
    config.initial_cols = 130
    config.initial_rows = 35
    config.font_size = 12
    config.font = wezterm.font 'Cascadia Code'

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
elseif triple:match('darwin') then
    -- macOS: zsh como shell de login
    config.default_prog = { 'zsh', '-l' }
    config.font_size = 12
    config.font = wezterm.font 'Hack Nerd Font'
elseif triple:match('linux') then
    -- Linux: bash como shell de login
    config.default_prog = { 'bash', '-l' }
    config.font_size = 12
    config.font = wezterm.font 'Hack Nerd Font'
else
    -- Otros sistemas Unix: bash como opción genérica
    config.default_prog = { 'bash', '-l' }
    config.font_size = 12
    config.font = wezterm.font 'Hack Nerd Font'
end

config.color_scheme = 'Tokyo Night Storm'

config.window_decorations = 'RESIZE'
-- Fondo de la ventana semitransparente (0.9 = 90 % opaco)
config.window_background_opacity = 0.95
config.use_fancy_tab_bar = false
config.hide_tab_bar_if_only_one_tab = false

config.window_padding = {
    left = 4,
    right = 4,
    top = 2,
    bottom = 2,
}

config.default_cursor_style = 'BlinkingBlock'

return config
