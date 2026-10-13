const express = require('express');
const os = require('os');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>Node.js App</title></head>
      <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 120px; background: #f4f9f4;">
        <h1 style="color: #3c873a;">Hello World from Node.js!</h1>
        <p>Express server running inside a Docker container</p>
        <p>Container hostname: <b>${os.hostname()}</b> | Node ${process.version}</p>
      </body>
    </html>`);
});

app.listen(PORT, () => console.log(`Node.js app listening on port ${PORT}`));
