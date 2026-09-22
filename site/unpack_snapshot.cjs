const fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const root=path.resolve('public');
const files=JSON.parse(zlib.gunzipSync(Buffer.concat(fs.readdirSync('.').filter(n=>/^snapshot\.\d+$/.test(n)).sort().map(n=>fs.readFileSync(n)))).toString());
fs.mkdirSync(root,{recursive:true});
for(const [name,data] of Object.entries(files)){
 const target=path.resolve(root,name);
 if(!target.startsWith(root+path.sep))throw Error('Invalid output path');
 fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,typeof data==='string'?data:Buffer.from(data.base64,'base64'));
}
console.log('Static site ready:',Object.keys(files).length,'files');
