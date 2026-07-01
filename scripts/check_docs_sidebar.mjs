import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  collectSidebarLinks,
  discoverSidebarPageLinks,
  generateSidebar
} from '../docs/.vitepress/sidebar.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DOCS_ROOT = path.join(ROOT, 'docs')

const sidebarLinks = collectSidebarLinks(generateSidebar({ docsRoot: DOCS_ROOT })).sort(compareLinks)
const expectedLinks = discoverSidebarPageLinks({ docsRoot: DOCS_ROOT })

const missingFromSidebar = expectedLinks.filter((link) => !sidebarLinks.includes(link))
const extraSidebarLinks = sidebarLinks.filter((link) => !expectedLinks.includes(link))
const missingTargets = sidebarLinks.filter((link) => !targetForLink(link).isFile)

if (missingFromSidebar.length || extraSidebarLinks.length || missingTargets.length) {
  printFailure('missing from generated sidebar', missingFromSidebar)
  printFailure('extra links in generated sidebar', extraSidebarLinks)
  printFailure(
    'generated sidebar links without matching markdown target',
    missingTargets.map((link) => `${link} -> ${targetForLink(link).path}`)
  )
  process.exit(1)
}

console.log(`docs sidebar ok: ${sidebarLinks.length} links generated`)

function targetForLink(link) {
  const route = link.replace(/^\//, '').replace(/\/$/, '')
  const target = link.endsWith('/')
    ? path.join(DOCS_ROOT, route, 'index.md')
    : path.join(DOCS_ROOT, `${route}.md`)

  return {
    path: path.relative(ROOT, target),
    isFile: fs.existsSync(target) && fs.statSync(target).isFile()
  }
}

function printFailure(label, items) {
  if (!items.length) {
    return
  }

  console.error(`${label}:`)
  for (const item of items) {
    console.error(`  - ${item}`)
  }
}

function compareLinks(left, right) {
  return left.localeCompare(right, 'en', {
    numeric: true,
    sensitivity: 'base'
  })
}
