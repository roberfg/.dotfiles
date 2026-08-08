return {
  {
    "stevearc/conform.nvim",
    event = { "BufReadPre", "BufNewFile" },
    cmd = { "ConformInfo" },
    config = function()
      require("conform").setup({
        formatters_by_ft = {
          lua = { "stylua" },
        },
        formatters = {
          stylua = {
            prepend_args = {
              "--indent-type",
              "Spaces",
              "--indent-width",
              "2",
            },
          },
        },
        format_on_save = {
          timeout_ms = 500,
          lsp_format = "fallback",
        },
      })

      vim.keymap.set({ "n", "v" }, "<leader>cf", function()
        require("conform").format({ async = true })
      end, { desc = "Formatear buffer" })
    end,
  },
}
