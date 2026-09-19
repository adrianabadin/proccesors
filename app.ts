import { JSDOM } from "jsdom"
import {existsSync, mkdirSync, writeFile} from "fs"
async function main(){
for (let i =2025;i<2026;i++){
const mainPage = await(await fetch(`https://hcd.saladillo.gob.ar/?f1=${i}&wpcfs=preset-1`,  {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
      },
    })).text()
const pagesForYear = getLastPageNumber(mainPage) || 1
for (let page=1;page<=pagesForYear;page++){
    const mainPage = await(await fetch(`https://hcd.saladillo.gob.ar/page/${page}/?f1=${i}&wpcfs=preset-1`,  {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
      },
    })).text()
    const linksPagina =getLinks(mainPage);
    linksPagina.forEach(async (link)=>{
    setTimeout(async ()=>{
        const ordenanza= await getOrdenanza(link)
        GuardarOrdenanza(ordenanza,link.titulo)
    },Math.random()*2000)
    console.log(link.titulo)
    })
}
}
    
// console.log(getLastPageNumber(mainPage))
// console.log(getLinks(mainPage))
//GuardarOrdenanza(await getOrdenanza({url:"https://hcd.saladillo.gob.ar/ordenanza/ordenanza-n-16-2025/",titulo:"texto"}),"Ordenanza N° 16/2025")
}

function getLastPageNumber(html:string):number | undefined{
const dom= new JSDOM(html).window.document
const div = dom.querySelector('div.numbers-navigation >a:last-child');

if (div !==null)
return parseInt(div.innerHTML.split("</span>")[1])
}
interface OrdenanzaLink {url:string,titulo:string}
function getLinks(html:string):OrdenanzaLink[]{
    const dom= new JSDOM(html).window.document
    const contenido = dom.querySelector("div.h-col >div >div:first-child")
const links =contenido?.querySelectorAll(" div >  a > h4")

const linksStr = links !== undefined ? Array.from(links).map(e=>({url:e.parentNode?.href,titulo:e.innerHTML})) :[]
links?.forEach(ee=>console.log(ee.innerHTML))
return linksStr
}
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
async function getOrdenanza(link:OrdenanzaLink){
  let cadena:string;
  console.log("Obteniendo ordenanza "+link.titulo)
 await sleep(Math.random() * 2000 + 1000);

  const html1= (await fetch(link.url,  {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
      },
    }))
    const html = await html1.text()
const document = new JSDOM(html).window.document
const contenido= document.getElementById("content")
const parrafos=contenido?.querySelectorAll("div > p")
 cadena =link.titulo+"\n";
parrafos?.forEach(e=>cadena+="\n"+e.textContent)

return cadena

    

}
async function GuardarOrdenanza(ordenanza:string,title:string){
    const anio = title.split("/")[1]
    if (!existsSync(`./${anio}`)) mkdirSync(`./${anio}`);
     writeFile(`./${anio}/${title.split("/")[0]}.txt`, ordenanza ||"","utf-8",(err)=>console.log(err));
}
main()