#!/bin/bash

# Vercel 部署问题一键修复脚本
# 使用方法: chmod +x fix-vercel-deployment.sh && ./fix-vercel-deployment.sh

echo "🚀 开始修复 Vercel 部署问题..."

# 1. 创建 @saasfly/auth 包的 env.mjs 文件
echo "📁 创建 env.mjs 文件..."
mkdir -p packages/auth
cp env.mjs packages/auth/env.mjs
echo "✅ env.mjs 文件已创建"

# 2. 备份并更新 next.config.mjs
echo "🔧 修复 next.config.mjs..."
if [ -f "apps/nextjs/next.config.mjs" ]; then
    cp apps/nextjs/next.config.mjs apps/nextjs/next.config.mjs.backup
    echo "📋 已备份原 next.config.mjs"
fi
mkdir -p apps/nextjs
cp next.config.mjs.fixed apps/nextjs/next.config.mjs
echo "✅ next.config.mjs 已修复"

# 3. 更新 package.json
echo "📦 修复 package.json..."
if [ -f "packages/auth/package.json" ]; then
    cp packages/auth/package.json packages/auth/package.json.backup
    echo "📋 已备份原 package.json"
fi
cp package.json.auth-fix packages/auth/package.json
echo "✅ package.json 已修复"

# 4. 安装必要依赖
echo "📥 安装依赖..."
bun add @t3-oss/env-nextjs zod
bun add -D @types/node typescript
echo "✅ 依赖安装完成"

# 5. 清理并重新构建
echo "🧹 清理缓存..."
rm -rf .next
rm -rf node_modules/.cache
rm -rf apps/nextjs/.next
echo "✅ 缓存清理完成"

# 6. 重新安装依赖
echo "🔄 重新安装依赖..."
bun install
echo "✅ 依赖重新安装完成"

# 7. 测试构建
echo "🔨 测试构建..."
if bun run build --filter=@saasfly/nextjs; then
    echo "✅ 构建成功！"
else
    echo "❌ 构建失败，请检查错误信息"
    exit 1
fi

echo ""
echo "🎉 修复完成！现在可以重新部署到 Vercel 了"
echo ""
echo "📝 请确保在 Vercel 项目设置中添加以下环境变量:"
echo "   - AUTH_SECRET=your-secret-key"
echo "   - AUTH_GITHUB_ID=your-github-id (可选)"
echo "   - AUTH_GITHUB_SECRET=your-github-secret (可选)"
echo "   - DATABASE_URL=your-database-url (可选)"
echo ""
echo "🚀 现在可以重新部署了！"