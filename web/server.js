const path = require('path')
const express = require("express")
const axios = require('axios')
const app = express()
const fs = require("fs")

require('dotenv').config()

const WEB_ROOT = process.env.WEB_ROOT
const API = process.env.API

console.log(WEB_ROOT)

const pathToIndex = path.join(WEB_ROOT, "/index.html")
function brand(req,res){
    let uuid = req.originalUrl.split("/")[2]
    const raw = fs.readFileSync(pathToIndex, 'utf8')
    axios
      .get(`https://api.feverdreams.app/v3/meta/${uuid}`)
      .then(api_res => { 
      let tp = `${uuid} - Created on Fever Dreams`
      let algo = "disco"
        if(api_res && api_res.data){
            if(api_res.data.algo) algo = api_res.data.algo
            if(algo==="disco"){
                tp = (api_res.data.text_prompts)?api_res.data.text_prompts:api_res.data.text_prompt
            }
            if(algo==="alpha" || algo ==="stable"){
                let private = api_res.data.private
                if(!private){
                    tp = api_res.data.params.prompt
                }else{
                    tp = "Rendered on Fever Dreams"
                }
            }
            if(!tp) tp = ""
            tp = tp.toString()
            tp = tp.replace("\"","")
            tp = tp.replace("<","$lt;")
            tp = tp.replace(">","$gt;")
            
            console.log(tp)
        }
          let updated = raw.replace(
              `<meta property="og:image" content="https://www.feverdreams.app/feverdream.png" data-react-helmet="true"/>`,
              `<meta property="og:image" content="https://images.feverdreams.app/jpg/${uuid}.jpg" data-react-helmet="true"/>`
          )
          updated = updated.replace(
              `<meta property="twitter:url" content="https://www.feverdreams.app">`,
              `<meta property="twitter:url" content="https://images.feverdreams.app/piece/${uuid}">`
          )
          updated = updated.replace(
              `<meta name="twitter:description" content="Create & Browse generative AI art created openly by other users.">`,
              `<meta name="twitter:description" content="${tp}">`
          )
          if(algo==="disco"){
            updated = updated.replace(
                `<meta name="twitter:image" content="https://www.feverdreams.app/feverdream.png">`,
                `<meta name="twitter:image" content="https://images.feverdreams.app/images/${uuid}0_0.png">`
            )
          }else{
            updated = updated.replace(
                `<meta name="twitter:image" content="https://www.feverdreams.app/feverdream.png">`,
                `<meta name="twitter:image" content="https://images.feverdreams.app/jpg/${uuid}.jpg">`
            )
          }
          updated = updated.replace(
              `<meta property="og:description" content="Create & Browse generative AI art created openly by other users." data-react-helmet="true"/>`,
              `<meta property="og:description" content="${tp}" data-react-helmet="true"/>`
          )
          res.send(updated)
      })
      .catch(error => {
          console.error(error);
          res.send(error);
      });
}
app.get("/piece/*", (req, res) => {
  brand(req,res)
})
app.get("/mutate/*", (req, res) => {
    brand(req,res)
})
app.get("/edit/*", (req, res) => {
    brand(req,res)
})


app.get("/gallery/*", (req, res) => {
    let discord_id = req.originalUrl.split("/")[2]
    const raw = fs.readFileSync(pathToIndex, 'utf8')
    axios
      .get(`https://api.feverdreams.app/user/${discord_id}`)
      .then(api_res => {        
          let updated = raw.replace(
              `<meta property="og:image" content="https://www.feverdreams.app/feverdream.png" data-react-helmet="true"/>`,
              `<meta property="og:image" content="${api_res.data.avatar}" data-react-helmet="true"/>`
          )
          updated = updated.replace(
              `<meta property="og:description" content="Create & Browse generative AI art created openly by other users." data-react-helmet="true"/>`,
              `<meta property="og:description" content="${api_res.data.display_name}'s Gallery" data-react-helmet="true"/>`
          )
          res.send(updated)
      })
      .catch(error => {
          console.error(error);
          res.send(error);
      });
  })

app.use(express.static(WEB_ROOT));

app.get("*", (req, res) =>{
    res.sendFile("index.html",{root:WEB_ROOT})
});

const port = process.env.PORT || 5000;
app.listen(port, () => {
	console.log(`Server started on port ${port}`);
})
