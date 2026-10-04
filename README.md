# App_1

A course that teaches people to code alongside LLMs.

## Getting started

```bash
pnpm install
pnpm dev
```

Open the URL it prints (usually http://localhost:5173).

## What is where

| Path                 | What it holds                            |
| -------------------- | ---------------------------------------- |
| `src/App.tsx`        | The page you see                         |
| `src/components/`    | Reusable pieces of interface             |
| `src/lib/lessons.ts` | Lesson content and the logic over it     |
| `src/index.css`      | Design tokens — colour, type, radius     |
| `CLAUDE.md`          | Conventions for humans and AI assistants |
| `tsconfig.json`      | TypeScript settings, annotated           |

## Commands

| Command           | What it does                                    |
| ----------------- | ----------------------------------------------- |
| `pnpm dev`        | Start the dev server with hot reload            |
| `pnpm check`      | Types + lint + format + tests, the full gate    |
| `pnpm test:watch` | Re-run tests as you edit                        |
| `pnpm build`      | Type-check, then produce `dist/` for deployment |
