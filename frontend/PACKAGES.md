# Frontend packages

Create the app (Node 20+):
```bash
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```
Extra packages (keep minimal):
```bash
npm install lucide-react     # icons (optional, 1 import per icon)
npm install zod              # runtime validation of API responses
```
Dev:
```bash
npm install -D prettier prettier-plugin-tailwindcss
```
Fonts: Space Mono via `next/font/google` (no package needed).
Run: `npm run dev` (http://localhost:3000)
