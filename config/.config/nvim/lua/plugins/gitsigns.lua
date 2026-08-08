return {
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      require("gitsigns").setup({
        signs = {
          add = { text = "▎" },
          change = { text = "▎" },
          delete = { text = "" },
          topdelete = { text = "" },
          changedelete = { text = "▎" },
        },
        on_attach = function(bufnr)
          local gs = package.loaded.gitsigns
          local map = function(keys, func, desc)
            vim.keymap.set("n", keys, func, { buffer = bufnr, desc = desc })
          end
          map("]h", gs.next_hunk, "Siguiente hunk")
          map("[h", gs.prev_hunk, "Hunk anterior")
          map("<leader>gp", gs.preview_hunk, "Preview hunk")
          map("<leader>gr", gs.reset_hunk, "Reset hunk")
          map("<leader>gb", gs.blame_line, "Blame línea")
          map("<leader>gd", gs.diffthis, "Diff")
        end,
      })
    end,
  },
  {
    "kdheepak/lazygit.nvim",
    cmd = "LazyGit",
    keys = {
      { "<leader>gg", "<cmd>LazyGit<cr>", desc = "LazyGit" },
    },
    dependencies = { "nvim-lua/plenary.nvim" },
  },
}
