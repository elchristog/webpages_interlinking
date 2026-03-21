import { _ as __vite_glob_0_0 } from './latinas-guia-oficial-1773871045_huLTBZW6.mjs';
import { c as createComponent, $ as $$LayoutA, a as $$LayoutC, b as $$Text, d as $$Wrapper } from './LayoutG_B6jv0ApT.mjs';
import 'piccolore';
import { r as renderComponent, a as renderTemplate, m as maybeRenderHead, b as addAttribute } from './prerender_CWH3BQVj.mjs';

async function getStaticPaths() {
  const articulos = Object.values([__vite_glob_0_0]);
  return articulos.map((articulo) => ({
    params: { slug: articulo.frontmatter.slug },
    props: { ...articulo }
  }));
}
const $$slug = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$slug;
  const { frontmatter, Content } = Astro2.props;
  let SelectedLayout = $$LayoutA;
  {
    SelectedLayout = $$LayoutC;
  }
  return renderTemplate`${renderComponent($$result, "SelectedLayout", SelectedLayout, { "titulo": frontmatter.titulo, "descripcion": frontmatter.descripcion }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<article> ${renderComponent($$result2, "Text", $$Text, { "tag": "h1", "variant": "displayMD", "class": "font-bold text-black tracking-tight mb-2" }, { "default": ($$result3) => renderTemplate`${frontmatter.titulo}` })} ${renderComponent($$result2, "Text", $$Text, { "tag": "p", "variant": "textSM", "class": "text-zinc-500 mb-8 border-b border-zinc-100 pb-4" }, { "default": ($$result3) => renderTemplate`
Publicado el: <time${addAttribute(frontmatter.fecha, "datetime")}>${frontmatter.fecha}</time> ` })} ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "prose" }, { "default": ($$result3) => renderTemplate` ${renderComponent($$result3, "Content", Content, {})} ` })} </article> ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/pages/blog/[slug].astro", void 0);

const $$file = "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/pages/blog/[slug].astro";
const $$url = "/blog/[slug]";

const _page = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$slug,
  file: $$file,
  getStaticPaths,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

const page = () => _page;

export { page };
