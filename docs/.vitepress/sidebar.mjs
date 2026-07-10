import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const CONFIG_DIR = path.dirname(fileURLToPath(import.meta.url))
const DEFAULT_DOCS_ROOT = path.resolve(CONFIG_DIR, '..')
const ACTIVE_PAGE_FILES = ['system.md', 'link.md', 'validation.md']

export function generateSidebar(options = {}) {
  const docsRoot = path.resolve(options.docsRoot ?? DEFAULT_DOCS_ROOT)
  const items = activePages(docsRoot).map((fileName) => ({
    text: pageTitle(path.join(docsRoot, fileName)),
    link: routeFor(fileName)
  }))

  return items.length ? [{ text: '规范', items }] : []
}

export function collectSidebarLinks(sidebar) {
  const links = []

  for (const item of sidebar) {
    collectLinks(item, links)
  }

  return links
}

export function discoverSidebarPageLinks(options = {}) {
  const docsRoot = path.resolve(options.docsRoot ?? DEFAULT_DOCS_ROOT)
  return activePages(docsRoot).map(routeFor)
}

function activePages(docsRoot) {
  return ACTIVE_PAGE_FILES.filter((fileName) => fs.existsSync(path.join(docsRoot, fileName)))
}

function collectLinks(item, links) {
  if (item.link) {
    links.push(item.link)
  }

  for (const child of item.items ?? []) {
    collectLinks(child, links)
  }
}

function pageTitle(filePath) {
  const text = fs.readFileSync(filePath, 'utf-8')
  return text.match(/^#\s+(.+)$/m)?.[1]?.trim() ?? path.basename(filePath, '.md')
}

function routeFor(fileName) {
  return '/' + path.basename(fileName, '.md')
}
