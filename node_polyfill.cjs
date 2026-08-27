const crypto = require('node:crypto');
if (!crypto.hash) {
  crypto.hash = function(algorithm, data, outputEncoding) {
    return crypto.createHash(algorithm).update(data).digest(outputEncoding);
  };
}
