#!/usr/bin/env node

import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { promises as fs } from 'node:fs';
import { build, context } from 'esbuild';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const rootDir = resolve(__dirname, '..', '..');
const distDir = resolve(__dirname, 'dist');
const templatePath = resolve(__dirname, 'autoOrder.template.user.js');
const userScriptPath = resolve(__dirname, 'autoOrder.user.js');

const buildTargets = [
  {
    name: 'auto-driver',
    entryPoint: resolve(__dirname, 'modules', 'autoDriver.js'),
    outfile: resolve(distDir, 'tradovate_auto_driver.js'),
    globalName: 'TradovateAutoDriverBundle',
  },
  {
    name: 'ui-panel',
    entryPoint: resolve(__dirname, 'modules', 'uiPanel.js'),
    outfile: resolve(distDir, 'tradovate_ui_panel.js'),
    globalName: 'TradovateUIPanelBundle',
  },
];

const args = process.argv.slice(2);
const watchMode = args.includes('--watch');

async function runBuild() {
  const buildOptions = (target) => ({
    entryPoints: [target.entryPoint],
    bundle: true,
    format: 'iife',
    target: ['es2020'],
    sourcemap: true,
    outfile: target.outfile,
    globalName: target.globalName,
    logLevel: 'info',
    minify: !watchMode,
    define: {
      'process.env.NODE_ENV': JSON.stringify(
        watchMode ? 'development' : 'production'
      ),
    },
  });

  try {
    if (watchMode) {
      await Promise.all(
        buildTargets.map(async (target) => {
          const ctx = await context(buildOptions(target));
          await ctx.watch({
            onRebuild(error) {
              if (error) {
                console.error(`[${target.name}] rebuild failed`, error);
              } else {
                console.log(`[${target.name}] rebuild complete`);
                updateUserScript().catch((err) =>
                  console.error('Failed to update autoOrder.user.js after rebuild', err)
                );
              }
            },
          });
          return ctx;
        })
      );
      console.log('Tampermonkey bundles watching for changes...');
      await updateUserScript();
      await new Promise(() => {});
    } else {
      await Promise.all(
        buildTargets.map((target) => build(buildOptions(target)))
      );
      await updateUserScript();
      console.log('Tampermonkey bundles built successfully');
    }
  } catch (error) {
    console.error('Tampermonkey bundle build failed', error);
    process.exitCode = 1;
  }
}

async function updateUserScript() {
  try {
    const [template, driverCode, panelCode] = await Promise.all([
      fs.readFile(templatePath, 'utf8'),
      fs.readFile(resolve(distDir, 'tradovate_auto_driver.js'), 'utf8'),
      fs.readFile(resolve(distDir, 'tradovate_ui_panel.js'), 'utf8'),
    ]);

    const content = template
      .replace('__AUTO_DRIVER_BUNDLE__', JSON.stringify(driverCode))
      .replace('__UI_PANEL_BUNDLE__', JSON.stringify(panelCode));

    await fs.writeFile(userScriptPath, content, 'utf8');
    console.log('Updated autoOrder.user.js with latest bundles');
  } catch (error) {
    console.error('Failed to update autoOrder.user.js', error);
    throw error;
  }
}

runBuild();
