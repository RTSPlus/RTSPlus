// import sha256 from "crypto-js/sha256";
var CryptoJS = require("crypto-js");

console.log("test");

// console.log(CryptoJS);
const nonce =
  "/api/v3/getroutes?requestType=getroutes&locale=en&key=Qskvu4Z5JDwGEVswqdAVkiA5B&format=json&xtime=1668654685831Thu, 17 Nov 2022 03:12:04 GMT";
const key = "";
console.log(CryptoJS.HmacSHA256(nonce, key).toString());
