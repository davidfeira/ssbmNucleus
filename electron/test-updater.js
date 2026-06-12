// Quick harness: run updater.check() outside Electron against the live manifest.
//   node electron/test-updater.js [fakeVersion]
const Module = require('module');
const origLoad = Module._load;
Module._load = function (request, ...rest) {
  if (request === 'electron') {
    return {
      app: {
        getVersion: () => process.argv[2] || '0.2.0',
        getPath: () => require('os').tmpdir(),
        quit: () => console.log('(app.quit called)'),
      },
    };
  }
  return origLoad.apply(this, [request, ...rest]);
};

const updater = require('./updater');
updater.check()
  .then((update) => {
    console.log('check() result:', JSON.stringify(update, null, 2));
  })
  .catch((err) => {
    console.error('check() failed:', err.message);
    process.exit(1);
  });
