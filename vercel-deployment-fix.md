# Vercel 部署问题完整解决方案

## 问题描述
```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/vercel/path0/node_modules/@saasfly/auth/env.mjs'
```

## 解决方案

### 1. 创建缺失的 env.mjs 文件

在 `packages/auth/` 或 `@saasfly/auth/` 目录下创建 `env.mjs` 文件：

```javascript
// packages/auth/env.mjs 或 node_modules/@saasfly/auth/env.mjs
import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    AUTH_SECRET: z.string().min(1),
    AUTH_GITHUB_ID: z.string().min(1).optional(),
    AUTH_GITHUB_SECRET: z.string().min(1).optional(),
    AUTH_GOOGLE_ID: z.string().min(1).optional(),
    AUTH_GOOGLE_SECRET: z.string().min(1).optional(),
    DATABASE_URL: z.string().min(1).optional(),
  },
  client: {},
  runtimeEnv: {
    AUTH_SECRET: process.env.AUTH_SECRET,
    AUTH_GITHUB_ID: process.env.AUTH_GITHUB_ID,
    AUTH_GITHUB_SECRET: process.env.AUTH_GITHUB_SECRET,
    AUTH_GOOGLE_ID: process.env.AUTH_GOOGLE_ID,
    AUTH_GOOGLE_SECRET: process.env.AUTH_GOOGLE_SECRET,
    DATABASE_URL: process.env.DATABASE_URL,
  },
});
```

### 2. 修复 next.config.mjs 导入路径

在 `apps/nextjs/next.config.mjs` 中修改导入：

```javascript
// 原来的导入（可能有问题）
// import { env } from "@saasfly/auth/env.mjs";

// 修复后的导入
import { env } from "@saasfly/auth/env";
// 或者使用相对路径
// import { env } from "../../packages/auth/env.mjs";
```

### 3. 更新 package.json 配置

在根目录的 `package.json` 中确保正确的工作区配置：

```json
{
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "packageManager": "bun@1.0.0"
}
```

在 `packages/auth/package.json` 中添加正确的导出：

```json
{
  "name": "@saasfly/auth",
  "exports": {
    "./env": "./env.mjs",
    "./env.mjs": "./env.mjs"
  },
  "files": [
    "env.mjs",
    "dist"
  ]
}
```

### 4. 创建 Vercel 构建配置

在根目录创建 `vercel.json`：

```json
{
  "buildCommand": "bun run build",
  "outputDirectory": "apps/nextjs/.next",
  "installCommand": "bun install",
  "framework": "nextjs",
  "functions": {
    "apps/nextjs/app/**/*.{js,ts,jsx,tsx}": {
      "runtime": "nodejs18.x"
    }
  }
}
```

### 5. 修复 turbo.json 配置

确保 `turbo.json` 包含正确的构建依赖：

```json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**"]
    },
    "@saasfly/nextjs#build": {
      "dependsOn": ["@saasfly/auth#build"],
      "outputs": [".next/**"]
    }
  }
}
```

### 6. 环境变量配置

在 Vercel 项目设置中添加必要的环境变量：

```bash
AUTH_SECRET=your-secret-key
AUTH_GITHUB_ID=your-github-id
AUTH_GITHUB_SECRET=your-github-secret
DATABASE_URL=your-database-url
```

### 7. 构建脚本修复

在 `apps/nextjs/package.json` 中确保构建脚本正确：

```json
{
  "scripts": {
    "build": "next build",
    "with-env": "dotenv -e ../../.env -- ",
    "dev": "bun with-env next dev"
  }
}
```

### 8. 依赖安装修复

确保所有必要的依赖都已安装：

```bash
bun add @t3-oss/env-nextjs zod
bun add -D @types/node
```

## 快速修复步骤

1. 创建 `packages/auth/env.mjs` 文件
2. 修改 `apps/nextjs/next.config.mjs` 中的导入路径
3. 更新 `packages/auth/package.json` 的 exports 字段
4. 在 Vercel 中设置环境变量
5. 重新部署

## 常见问题

- **模块路径问题**: 确保导入路径与实际文件结构匹配
- **工作区配置**: 检查 monorepo 的工作区配置是否正确
- **环境变量**: 确保所有必需的环境变量都已设置
- **构建顺序**: 确保依赖包在主应用之前构建

按照以上步骤操作应该能完全解决 Vercel 部署问题。