return {
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    config = function()
      local wk = require("which-key")
      wk.setup({
        preset = "modern",
        delay = 300,
      })

      wk.add({
        { "<leader>c", group = "Código / LSP" },
        { "<leader>f", group = "Buscar" },
        { "<leader>g", group = "Git" },
      })
    end,
  },
}
