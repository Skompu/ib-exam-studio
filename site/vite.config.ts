import { defineConfig } from "vite";
import { cloudflare } from "@cloudflare/vite-plugin";
import { whop } from "@whop/cli/vite";

export default defineConfig({
  plugins: [
    cloudflare({ viteEnvironment: { name: "server" } }),
    whop({ disableTanstackDevtools: true }),
  ],
});
