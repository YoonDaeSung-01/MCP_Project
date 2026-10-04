import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';

// This script renders documentation. It does not start the App.
const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const rendererDirArg = process.argv[2];
const configFileArg = process.argv[3] ?? 'docs/diagrams/diagram-config.json';
const fence = String.fromCharCode(96).repeat(3);

if (!rendererDirArg) {
  throw new Error('Usage: node scripts/render_docs.mjs <renderer-package-directory> [config-file]');
}

function resolveWorkspacePath(value) {
  const resolved = path.resolve(rootDir, value);
  const relative = path.relative(rootDir, resolved);
  if (relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) {
    throw new Error('The documentation path is outside the workspace: ' + value);
  }
  return resolved;
}

function escapeXml(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;'
  })[character]);
}

function readDiagrams(content, sourceName) {
  const lines = content.split(/\r?\n/);
  const diagrams = [];
  for (let index = 0; index < lines.length; index += 1) {
    const marker = lines[index].trim().match(/^<!-- diagram: ([a-z0-9-]+) -->$/);
    if (!marker) continue;
    let start = index + 1;
    while (start < lines.length && lines[start].trim() === '') start += 1;
    if (lines[start]?.trim() !== fence + 'mermaid') {
      throw new Error('The diagram marker has no Mermaid source: ' + sourceName + ':' + (index + 1));
    }
    let end = start + 1;
    while (end < lines.length && lines[end].trim() !== fence) end += 1;
    if (end === lines.length) {
      throw new Error('The Mermaid source has no closing fence: ' + sourceName);
    }
    diagrams.push({
      id: marker[1],
      sourceFile: sourceName,
      sourceLine: start + 2,
      source: lines.slice(start + 1, end).join('\n').trim()
    });
    index = end;
  }
  return diagrams;
}

const config = JSON.parse(await fs.readFile(resolveWorkspacePath(configFileArg), 'utf8'));
const rendererDir = path.resolve(rendererDirArg);
const rendererPackage = JSON.parse(await fs.readFile(path.join(rendererDir, 'package.json'), 'utf8'));
if (rendererPackage.name !== config.renderer || rendererPackage.version !== config.rendererVersion) {
  throw new Error('Install the documentation renderer version from diagram-config.json.');
}
const rendererEntry = rendererPackage.exports?.['.']?.import;
if (typeof rendererEntry !== 'string') {
  throw new Error('The renderer package has no supported ESM entry.');
}
const { renderMermaidSVG } = await import(pathToFileURL(path.resolve(rendererDir, rendererEntry)).href);
if (typeof renderMermaidSVG !== 'function') {
  throw new Error('The renderer does not provide renderMermaidSVG.');
}

const diagrams = [];
for (const sourceName of config.sources) {
  const content = await fs.readFile(resolveWorkspacePath(sourceName), 'utf8');
  diagrams.push(...readDiagrams(content, sourceName));
}
if (diagrams.length === 0) throw new Error('No documentation diagrams were found.');
const ids = new Set();
const outputs = [];
for (const diagram of diagrams) {
  if (ids.has(diagram.id)) throw new Error('Duplicate diagram ID: ' + diagram.id);
  ids.add(diagram.id);
  const title = config.titles[diagram.id];
  if (!title) throw new Error('The diagram title is missing: ' + diagram.id);
  const rendered = renderMermaidSVG(diagram.source, config.renderOptions);
  const svg = rendered.replace(/<svg\b[^>]*>/, (tag) => tag + '<title>' + escapeXml(title) + '</title>');
  if (!svg.includes('<svg') || !svg.includes('</svg>')) {
    throw new Error('The renderer returned an invalid SVG: ' + diagram.id);
  }
  outputs.push({
    filename: diagram.id + '.svg',
    svg,
    metadata: {
      id: diagram.id,
      title,
      sourceFile: diagram.sourceFile,
      sourceLine: diagram.sourceLine,
      sourceSha256: createHash('sha256').update(diagram.source).digest('hex'),
      svgSha256: createHash('sha256').update(svg).digest('hex')
    }
  });
}

const outputDir = resolveWorkspacePath(config.outputDirectory);
await fs.mkdir(outputDir, { recursive: true });
for (const output of outputs) {
  await fs.writeFile(path.join(outputDir, output.filename), output.svg, 'utf8');
}
const manifest = {
  renderer: rendererPackage.name,
  rendererVersion: rendererPackage.version,
  configFile: configFileArg,
  configSha256: createHash('sha256').update(JSON.stringify(config)).digest('hex'),
  diagrams: outputs.map((output) => output.metadata)
};
await fs.writeFile(path.join(outputDir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ rendered: outputs.length, renderer: manifest.renderer, version: manifest.rendererVersion }));
