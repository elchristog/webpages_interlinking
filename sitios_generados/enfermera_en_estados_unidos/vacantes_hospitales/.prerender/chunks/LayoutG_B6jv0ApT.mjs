import 'piccolore';
import { t as typeHandlers, c as types, A as AstroError, N as NoImageMetadata, F as FailedToFetchRemoteImageDimensions, R as RemoteImageNotAllowed, I as InvalidComponentArgs, d as createRenderInstruction, r as renderComponent, e as Fragment, a as renderTemplate, u as unescapeHTML, b as addAttribute, m as maybeRenderHead, f as renderSlot, g as defineStyleVars, h as renderHead, E as ExpectedImage, L as LocalImageUsedWrongly, M as MissingImageDimension, U as UnsupportedImageFormat, i as IncompatibleDescriptorOptions, j as UnsupportedImageConversion, k as ExpectedImageOptions, l as ExpectedNotESMImage, n as InvalidImageService, o as ImageMissingAlt, s as spreadAttributes, p as FontFamilyNotFound } from './prerender_CWH3BQVj.mjs';
import 'clsx';
import { joinPaths, isRemotePath } from '@astrojs/internal-helpers/path';
import { isRemoteAllowed } from '@astrojs/internal-helpers/remote';
import * as mime from 'mrmime';
import { escape } from 'html-escaper';

function isESMImportedImage(src) {
  return typeof src === "object" || typeof src === "function" && "src" in src;
}
function isRemoteImage(src) {
  return typeof src === "string";
}
async function resolveSrc(src) {
  if (typeof src === "object" && "then" in src) {
    const resource = await src;
    return resource.default ?? resource;
  }
  return src;
}

const firstBytes = /* @__PURE__ */ new Map([
  [0, "heif"],
  [56, "psd"],
  [66, "bmp"],
  [68, "dds"],
  [71, "gif"],
  [73, "tiff"],
  [77, "tiff"],
  [82, "webp"],
  [105, "icns"],
  [137, "png"],
  [255, "jpg"]
]);
function detector(input) {
  const byte = input[0];
  const type = firstBytes.get(byte);
  if (type && typeHandlers.get(type).validate(input)) {
    return type;
  }
  return types.find((imageType) => typeHandlers.get(imageType).validate(input));
}

function lookup(input) {
  const type = detector(input);
  if (typeof type !== "undefined") {
    const size = typeHandlers.get(type).calculate(input);
    if (size !== void 0) {
      size.type = size.type ?? type;
      return size;
    }
  }
  throw new TypeError("unsupported file type: " + type);
}

async function imageMetadata(data, src) {
  let result;
  try {
    result = lookup(data);
  } catch {
    throw new AstroError({
      ...NoImageMetadata,
      message: NoImageMetadata.message(src)
    });
  }
  if (!result.height || !result.width || !result.type) {
    throw new AstroError({
      ...NoImageMetadata,
      message: NoImageMetadata.message(src)
    });
  }
  const { width, height, type, orientation } = result;
  const isPortrait = (orientation || 0) >= 5;
  return {
    width: isPortrait ? height : width,
    height: isPortrait ? width : height,
    format: type,
    orientation
  };
}

async function inferRemoteSize(url, imageConfig) {
  if (!URL.canParse(url)) {
    throw new AstroError({
      ...FailedToFetchRemoteImageDimensions,
      message: FailedToFetchRemoteImageDimensions.message(url)
    });
  }
  const allowlistConfig = imageConfig ? {
    domains: imageConfig.domains ?? [],
    remotePatterns: imageConfig.remotePatterns ?? []
  } : void 0;
  if (!allowlistConfig) {
    const parsedUrl = new URL(url);
    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      throw new AstroError({
        ...FailedToFetchRemoteImageDimensions,
        message: FailedToFetchRemoteImageDimensions.message(url)
      });
    }
  }
  if (allowlistConfig && !isRemoteAllowed(url, allowlistConfig)) {
    throw new AstroError({
      ...RemoteImageNotAllowed,
      message: RemoteImageNotAllowed.message(url)
    });
  }
  const response = await fetch(url, { redirect: "manual" });
  if (response.status >= 300 && response.status < 400) {
    throw new AstroError({
      ...FailedToFetchRemoteImageDimensions,
      message: FailedToFetchRemoteImageDimensions.message(url)
    });
  }
  if (!response.body || !response.ok) {
    throw new AstroError({
      ...FailedToFetchRemoteImageDimensions,
      message: FailedToFetchRemoteImageDimensions.message(url)
    });
  }
  const reader = response.body.getReader();
  let done, value;
  let accumulatedChunks = new Uint8Array();
  while (!done) {
    const readResult = await reader.read();
    done = readResult.done;
    if (done) break;
    if (readResult.value) {
      value = readResult.value;
      let tmp = new Uint8Array(accumulatedChunks.length + value.length);
      tmp.set(accumulatedChunks, 0);
      tmp.set(value, accumulatedChunks.length);
      accumulatedChunks = tmp;
      try {
        const dimensions = await imageMetadata(accumulatedChunks, url);
        if (dimensions) {
          await reader.cancel();
          return dimensions;
        }
      } catch {
      }
    }
  }
  throw new AstroError({
    ...NoImageMetadata,
    message: NoImageMetadata.message(url)
  });
}

function validateArgs(args) {
  if (args.length !== 3) return false;
  if (!args[0] || typeof args[0] !== "object") return false;
  return true;
}
function baseCreateComponent(cb, moduleId, propagation) {
  const name = moduleId?.split("/").pop()?.replace(".astro", "") ?? "";
  const fn = (...args) => {
    if (!validateArgs(args)) {
      throw new AstroError({
        ...InvalidComponentArgs,
        message: InvalidComponentArgs.message(name)
      });
    }
    return cb(...args);
  };
  Object.defineProperty(fn, "name", { value: name, writable: false });
  fn.isAstroComponentFactory = true;
  fn.moduleId = moduleId;
  fn.propagation = propagation;
  return fn;
}
function createComponentWithOptions(opts) {
  const cb = baseCreateComponent(opts.factory, opts.moduleId, opts.propagation);
  return cb;
}
function createComponent(arg1, moduleId, propagation) {
  if (typeof arg1 === "function") {
    return baseCreateComponent(arg1, moduleId, propagation);
  } else {
    return createComponentWithOptions(arg1);
  }
}

async function renderScript(result, id) {
  const inlined = result.inlinedScripts.get(id);
  let content = "";
  if (inlined != null) {
    if (inlined) {
      content = `<script type="module">${inlined}</script>`;
    }
  } else {
    const resolved = await result.resolve(id);
    content = `<script type="module" src="${result.userAssetsBase ? (result.base === "/" ? "" : result.base) + result.userAssetsBase : ""}${resolved}"></script>`;
  }
  return createRenderInstruction({ type: "script", id, content });
}

const createMetaTag = (attributes) => {
  const attrs = Object.entries(attributes).map(([key, value]) => `${key}="${escape(value)}"`).join(" ");
  return `<meta ${attrs}>`;
};
const createLinkTag = (attributes) => {
  const attrs = Object.entries(attributes).map(([key, value]) => `${key}="${escape(value)}"`).join(" ");
  return `<link ${attrs}>`;
};
const createOpenGraphTag = (property, content) => {
  return createMetaTag({ property: `og:${property}`, content });
};
const buildOpenGraphMediaTags = (mediaType, media) => {
  let tags = "";
  const addTag = (tag) => {
    tags += tag + "\n";
  };
  media.forEach((medium) => {
    addTag(createOpenGraphTag(mediaType, medium.url));
    if (medium.alt) {
      addTag(createOpenGraphTag(`${mediaType}:alt`, medium.alt));
    }
    if (medium.secureUrl) {
      addTag(createOpenGraphTag(`${mediaType}:secure_url`, medium.secureUrl));
    }
    if (medium.type) {
      addTag(createOpenGraphTag(`${mediaType}:type`, medium.type));
    }
    if (medium.width) {
      addTag(createOpenGraphTag(`${mediaType}:width`, medium.width.toString()));
    }
    if (medium.height) {
      addTag(
        createOpenGraphTag(`${mediaType}:height`, medium.height.toString())
      );
    }
  });
  return tags;
};
const buildTags = (config) => {
  let tagsToRender = "";
  const addTag = (tag) => {
    tagsToRender += tag + "\n";
  };
  if (config.title) {
    const formattedTitle = config.titleTemplate ? config.titleTemplate.replace("%s", config.title) : config.title;
    addTag(`<title>${escape(formattedTitle)}</title>`);
  }
  if (config.description) {
    addTag(createMetaTag({ name: "description", content: config.description }));
  }
  let robotsContent = [];
  if (typeof config.noindex !== "undefined") {
    robotsContent.push(config.noindex ? "noindex" : "index");
  }
  if (typeof config.nofollow !== "undefined") {
    robotsContent.push(config.nofollow ? "nofollow" : "follow");
  }
  if (config.robotsProps) {
    const {
      nosnippet,
      maxSnippet,
      maxImagePreview,
      noarchive,
      unavailableAfter,
      noimageindex,
      notranslate
    } = config.robotsProps;
    if (nosnippet) robotsContent.push("nosnippet");
    if (typeof maxSnippet === "number") robotsContent.push(`max-snippet:${maxSnippet}`);
    if (maxImagePreview)
      robotsContent.push(`max-image-preview:${maxImagePreview}`);
    if (noarchive) robotsContent.push("noarchive");
    if (unavailableAfter)
      robotsContent.push(`unavailable_after:${unavailableAfter}`);
    if (noimageindex) robotsContent.push("noimageindex");
    if (notranslate) robotsContent.push("notranslate");
  }
  if (robotsContent.length > 0) {
    addTag(createMetaTag({ name: "robots", content: robotsContent.join(",") }));
  }
  if (config.canonical) {
    addTag(createLinkTag({ rel: "canonical", href: config.canonical }));
  }
  if (config.mobileAlternate) {
    addTag(
      createLinkTag({
        rel: "alternate",
        media: config.mobileAlternate.media,
        href: config.mobileAlternate.href
      })
    );
  }
  if (config.languageAlternates && config.languageAlternates.length > 0) {
    config.languageAlternates.forEach((languageAlternate) => {
      addTag(
        createLinkTag({
          rel: "alternate",
          hreflang: languageAlternate.hreflang,
          href: languageAlternate.href
        })
      );
    });
  }
  if (config.openGraph) {
    const title = config.openGraph?.title || config.title;
    if (title) {
      addTag(createOpenGraphTag("title", title));
    }
    const description = config.openGraph?.description || config.description;
    if (description) {
      addTag(createOpenGraphTag("description", description));
    }
    if (config.openGraph.url) {
      addTag(createOpenGraphTag("url", config.openGraph.url));
    }
    if (config.openGraph.type) {
      addTag(createOpenGraphTag("type", config.openGraph.type));
    }
    if (config.openGraph.images && config.openGraph.images.length) {
      addTag(buildOpenGraphMediaTags("image", config.openGraph.images));
    }
    if (config.openGraph.videos && config.openGraph.videos.length) {
      addTag(buildOpenGraphMediaTags("video", config.openGraph.videos));
    }
    if (config.openGraph.locale) {
      addTag(createOpenGraphTag("locale", config.openGraph.locale));
    }
    if (config.openGraph.site_name) {
      addTag(createOpenGraphTag("site_name", config.openGraph.site_name));
    }
    if (config.openGraph.profile) {
      if (config.openGraph.profile.firstName) {
        addTag(
          createOpenGraphTag(
            "profile:first_name",
            config.openGraph.profile.firstName
          )
        );
      }
      if (config.openGraph.profile.lastName) {
        addTag(
          createOpenGraphTag(
            "profile:last_name",
            config.openGraph.profile.lastName
          )
        );
      }
      if (config.openGraph.profile.username) {
        addTag(
          createOpenGraphTag(
            "profile:username",
            config.openGraph.profile.username
          )
        );
      }
      if (config.openGraph.profile.gender) {
        addTag(
          createOpenGraphTag("profile:gender", config.openGraph.profile.gender)
        );
      }
    }
    if (config.openGraph.book) {
      if (config.openGraph.book.authors && config.openGraph.book.authors.length) {
        config.openGraph.book.authors.forEach((author) => {
          addTag(createOpenGraphTag("book:author", author));
        });
      }
      if (config.openGraph.book.isbn) {
        addTag(createOpenGraphTag("book:isbn", config.openGraph.book.isbn));
      }
      if (config.openGraph.book.releaseDate) {
        addTag(
          createOpenGraphTag(
            "book:release_date",
            config.openGraph.book.releaseDate
          )
        );
      }
      if (config.openGraph.book.tags && config.openGraph.book.tags.length) {
        config.openGraph.book.tags.forEach((tag) => {
          addTag(createOpenGraphTag("book:tag", tag));
        });
      }
    }
    if (config.openGraph.article) {
      if (config.openGraph.article.publishedTime) {
        addTag(
          createOpenGraphTag(
            "article:published_time",
            config.openGraph.article.publishedTime
          )
        );
      }
      if (config.openGraph.article.modifiedTime) {
        addTag(
          createOpenGraphTag(
            "article:modified_time",
            config.openGraph.article.modifiedTime
          )
        );
      }
      if (config.openGraph.article.expirationTime) {
        addTag(
          createOpenGraphTag(
            "article:expiration_time",
            config.openGraph.article.expirationTime
          )
        );
      }
      if (config.openGraph.article.authors && config.openGraph.article.authors.length) {
        config.openGraph.article.authors.forEach((author) => {
          addTag(createOpenGraphTag("article:author", author));
        });
      }
      if (config.openGraph.article.section) {
        addTag(
          createOpenGraphTag(
            "article:section",
            config.openGraph.article.section
          )
        );
      }
      if (config.openGraph.article.tags && config.openGraph.article.tags.length) {
        config.openGraph.article.tags.forEach((tag) => {
          addTag(createOpenGraphTag("article:tag", tag));
        });
      }
    }
    if (config.openGraph.video) {
      if (config.openGraph.video.actors && config.openGraph.video.actors.length) {
        config.openGraph.video.actors.forEach((actor) => {
          addTag(createOpenGraphTag("video:actor", actor.profile));
          if (actor.role) {
            addTag(createOpenGraphTag("video:actor:role", actor.role));
          }
        });
      }
      if (config.openGraph.video.directors && config.openGraph.video.directors.length) {
        config.openGraph.video.directors.forEach((director) => {
          addTag(createOpenGraphTag("video:director", director));
        });
      }
      if (config.openGraph.video.writers && config.openGraph.video.writers.length) {
        config.openGraph.video.writers.forEach((writer) => {
          addTag(createOpenGraphTag("video:writer", writer));
        });
      }
      if (config.openGraph.video.duration) {
        addTag(
          createOpenGraphTag(
            "video:duration",
            config.openGraph.video.duration.toString()
          )
        );
      }
      if (config.openGraph.video.releaseDate) {
        addTag(
          createOpenGraphTag(
            "video:release_date",
            config.openGraph.video.releaseDate
          )
        );
      }
      if (config.openGraph.video.tags && config.openGraph.video.tags.length) {
        config.openGraph.video.tags.forEach((tag) => {
          addTag(createOpenGraphTag("video:tag", tag));
        });
      }
      if (config.openGraph.video.series) {
        addTag(
          createOpenGraphTag("video:series", config.openGraph.video.series)
        );
      }
    }
  }
  if (config.facebook && config.facebook.appId) {
    addTag(
      createMetaTag({ property: "fb:app_id", content: config.facebook.appId })
    );
  }
  if (config.twitter) {
    if (config.twitter.cardType) {
      addTag(
        createMetaTag({
          name: "twitter:card",
          content: config.twitter.cardType
        })
      );
    }
    if (config.twitter.site) {
      addTag(
        createMetaTag({ name: "twitter:site", content: config.twitter.site })
      );
    }
    if (config.twitter.handle) {
      addTag(
        createMetaTag({
          name: "twitter:creator",
          content: config.twitter.handle
        })
      );
    }
  }
  if (config.additionalMetaTags && config.additionalMetaTags.length > 0) {
    config.additionalMetaTags.forEach((metaTag) => {
      const attributes = {
        content: metaTag.content
      };
      if ("name" in metaTag && metaTag.name) {
        attributes.name = metaTag.name;
      } else if ("property" in metaTag && metaTag.property) {
        attributes.property = metaTag.property;
      } else if ("httpEquiv" in metaTag && metaTag.httpEquiv) {
        attributes["http-equiv"] = metaTag.httpEquiv;
      }
      addTag(createMetaTag(attributes));
    });
  }
  if (config.additionalLinkTags && config.additionalLinkTags.length > 0) {
    config.additionalLinkTags.forEach((linkTag) => {
      const attributes = {
        rel: linkTag.rel,
        href: linkTag.href
      };
      if (linkTag.sizes) {
        attributes.sizes = linkTag.sizes;
      }
      if (linkTag.media) {
        attributes.media = linkTag.media;
      }
      if (linkTag.type) {
        attributes.type = linkTag.type;
      }
      if (linkTag.color) {
        attributes.color = linkTag.color;
      }
      if (linkTag.as) {
        attributes.as = linkTag.as;
      }
      if (linkTag.crossOrigin) {
        attributes.crossorigin = linkTag.crossOrigin;
      }
      addTag(createLinkTag(attributes));
    });
  }
  return tagsToRender.trim();
};

const $$AstroSeo = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$AstroSeo;
  const {
    title,
    titleTemplate,
    noindex,
    nofollow,
    robotsProps,
    description,
    canonical,
    mobileAlternate,
    languageAlternates,
    openGraph,
    facebook,
    twitter,
    additionalMetaTags,
    additionalLinkTags
  } = Astro2.props;
  return renderTemplate`${renderComponent($$result, "Fragment", Fragment, {}, { "default": ($$result2) => renderTemplate`${unescapeHTML(buildTags({
    title,
    titleTemplate,
    noindex,
    nofollow,
    robotsProps,
    description,
    canonical,
    mobileAlternate,
    languageAlternates,
    openGraph,
    facebook,
    twitter,
    additionalMetaTags,
    additionalLinkTags
  }))}` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/node_modules/@lexingtonthemes/seo/src/AstroSeo.astro", void 0);

const nombre_sitio = "Travel Nurse Hispanas";
const seo = {"titulo_base":"Travel Nurses USA","descripcion_base":"Ofertas agresivas y sueldos astronómicos para enfermeras que viajan dentro de Estados Unidos.","idioma":"es-US"};
const footer = {"empresa_legal":"Enfermera en Estados Unidos","direccion":"Denver, CO 80201","email_contacto":"hola@travel-nurse-hispanas.org"};
const menu_global = [{"nombre":"Diploma Online","ruta":"/homologacion"},{"nombre":"Estudio NCLEX","ruta":"/nclex"},{"nombre":"Trabajo Hoy","ruta":"/vacantes"},{"nombre":"Visa EB-3","ruta":"/visa"},{"nombre":"Sueldo Promedio","ruta":"/salarios"},{"nombre":"Novedades","ruta":"/blog"},{"nombre":"Hablar Asesor","ruta":"https://wa.me/something"},{"nombre":"Entrar","ruta":"/login"}];
const dominio = "https://travel-nurse-hispanas.org";
const font_family = "Roboto";
const color_palette = {"primary":"hsl(260, 92%, 50%)","secondary":"hsl(290, 72%, 50%)","accent":"hsl(80, 92%, 26%)","text_bold":"hsl(260, 92%, 15%)"};
const config = {
  nombre_sitio,
  seo,
  footer,
  menu_global,
  dominio,
  font_family,
  color_palette};

const $$Seo = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Seo;
  const { titulo, descripcion } = Astro2.props;
  const title = titulo ? `${titulo} | ${config.seo.titulo_base}` : config.nombre_sitio;
  const description = descripcion || config.seo.descripcion_base;
  return renderTemplate`${renderComponent($$result, "AstroSeo", $$AstroSeo, { "title": title, "description": description, "canonical": config.dominio, "openGraph": {
    url: config.dominio,
    title,
    description,
    images: [
      {
        url: `${config.dominio}/og-image.jpg`,
        width: 1200,
        height: 630,
        alt: title,
        type: "image/jpeg"
      }
    ],
    site_name: config.nombre_sitio,
    type: "website",
    locale: config.seo.idioma.replace("-", "_")
  }, "twitter": {
    handle: "@enfermeraeeu",
    site: config.dominio,
    cardType: "summary_large_image"
  } })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/head/Seo.astro", void 0);

const $$Meta = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Meta;
  return renderTemplate`<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="geo.region" content="US"><meta name="geo.placename"${addAttribute(config.footer.direccion, "content")}><meta name="generator"${addAttribute(Astro2.generator, "content")}>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/head/Meta.astro", void 0);

const $$Fonts = createComponent(($$result, $$props, $$slots) => {
  const fontFamyly = config.font_family;
  const fontMap = {
    "Inter": "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
    "Roboto": "https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap",
    "Outfit": "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap",
    "Plus Jakarta Sans": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap"
  };
  const fontUrl = fontMap[fontFamyly];
  return renderTemplate`<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link${addAttribute(fontUrl, "href")} rel="stylesheet">`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/head/Fonts.astro", void 0);

const $$Favicons = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`<link rel="icon" type="image/svg+xml" href="/favicon.svg">`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/head/Favicons.astro", void 0);

const $$FuseJS = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`${renderScript($$result, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/scripts/FuseJS.astro?astro&type=script&index=0&lang.ts")}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/scripts/FuseJS.astro", void 0);

const $$KeenSlider = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`<link href="https://cdn.jsdelivr.net/npm/keen-slider@6.8.6/keen-slider.min.css" rel="stylesheet">`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/scripts/KeenSlider.astro", void 0);

const $$BaseHead = createComponent(($$result, $$props, $$slots) => {
  return renderTemplate`${renderComponent($$result, "Seo", $$Seo, {})} ${renderComponent($$result, "Meta", $$Meta, {})} ${renderComponent($$result, "Fonts", $$Fonts, {})} ${renderComponent($$result, "Favicons", $$Favicons, {})} <!-- Scripts --> ${renderComponent($$result, "FuseJs", $$FuseJS, {})} ${renderComponent($$result, "KeenSlider", $$KeenSlider, {})}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/head/BaseHead.astro", void 0);

const $$Logo = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Logo;
  const { class: className } = Astro2.props;
  return renderTemplate`${maybeRenderHead()}<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"${addAttribute(className, "class")}> <path d="M12 2L2 7l10 5 10-5-10-5z"></path> <path d="m2 17 10 5 10-5"></path> <path d="m2 12 10 5 10-5"></path> </svg>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/assets/Logo.astro", void 0);

const $$Button = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Button;
  const {
    variant = "default",
    size = "md",
    isLink = false,
    href = "#",
    class: className = "",
    type = "button",
    id
  } = Astro2.props;
  const baseStyles = "inline-flex items-center justify-center font-medium transition-colors duration-200 focus:outline-none";
  const variants = {
    default: "bg-[var(--color-primary)] text-white hover:opacity-90",
    muted: "bg-zinc-100 text-zinc-900 hover:bg-zinc-200",
    accent: "bg-[var(--color-accent)] text-white hover:opacity-90"
  };
  const sizes = {
    md: "px-4 py-2 text-sm",
    xl: "px-8 py-3 text-base"
  };
  const combinedClasses = `${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`;
  return renderTemplate`${isLink ? renderTemplate`${maybeRenderHead()}<a${addAttribute(href, "href")}${addAttribute(combinedClasses, "class")}${addAttribute(id, "id")}>${renderSlot($$result, $$slots["default"])}</a>` : renderTemplate`<button${addAttribute(type, "type")}${addAttribute(combinedClasses, "class")}${addAttribute(id, "id")}>${renderSlot($$result, $$slots["default"])}</button>`}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/elements/Button.astro", void 0);

var __freeze$2 = Object.freeze;
var __defProp$2 = Object.defineProperty;
var __template$2 = (cooked, raw) => __freeze$2(__defProp$2(cooked, "raw", { value: __freeze$2(cooked.slice()) }));
var _a$2;
const $$Navigation = createComponent(($$result, $$props, $$slots) => {
  const menuItems = config.menu_global || [];
  return renderTemplate(_a$2 || (_a$2 = __template$2(["", '<header class="fixed z-50 w-full top-4 md:px-12"> <div class="px-8 md:px-0 mx-auto 2xl:px-12 max-w-screen 2xl:max-w-[1440px]"> <div class="flex flex-col w-full bg-white md:items-center md:justify-between md:flex-row outline outline-base-200"> <div class="flex flex-row items-center justify-between w-full md:w-auto"> <a href="/" class="font-mono text-base font-bold uppercase bg-[var(--color-primary)]" aria-label="Home"> ', ' </a> <button class="relative z-50 text-white bg-[var(--color-primary)] md:hidden focus:outline-none focus:shadow-outline size-11" aria-label="Toggle navigation menu" id="navToggle"> <span class="sr-only">Toggle navigation</span> <svg class="mx-auto size-7" stroke="currentColor" fill="none" viewBox="0 0 24 24"> <path id="menuIcon" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path> <path id="closeIcon" class="hidden" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path> </svg> </button> </div> <!-- Fullscreen nav on mobile --> <nav id="navMenu" class="fixed inset-0 z-40 flex-col hidden w-full p-8 mt-20 bg-white md:mt-0 md:p-0 md:border-l md:border-base-200 md:items-center md:justify-end gap-2 md:gap-px sm:relative md:flex md:flex-row md:bg-transparent md:static" role="navigation" aria-label="Main navigation"> ', " ", ' </nav> </div> </div> <script type="module">\n    document.addEventListener("DOMContentLoaded", function () {\n      const toggle = document.getElementById("navToggle");\n      const nav = document.getElementById("navMenu");\n      const menuIcon = document.getElementById("menuIcon");\n      const closeIcon = document.getElementById("closeIcon");\n\n      // Mobile menu toggle\n      toggle.addEventListener("click", () => {\n        const isOpen = nav.classList.contains("flex");\n        nav.classList.toggle("hidden", isOpen);\n        nav.classList.toggle("flex", !isOpen);\n        menuIcon.classList.toggle("hidden", !isOpen);\n        closeIcon.classList.toggle("hidden", isOpen);\n      });\n    });\n  <\/script> </header>'])), maybeRenderHead(), renderComponent($$result, "Logo", $$Logo, { "class": "h-full p-2 text-white size-11" }), menuItems.map((item) => renderTemplate`${renderComponent($$result, "Button", $$Button, { "isLink": true, "size": "md", "variant": "muted", "href": item.ruta, "class": "w-full md:w-auto justify-start md:justify-center" }, { "default": ($$result2) => renderTemplate`${item.nombre}` })}`), renderComponent($$result, "Button", $$Button, { "isLink": true, "href": "/", "size": "md", "variant": "default", "class": "bg-black text-white px-6" }, { "default": ($$result2) => renderTemplate`
Contactar
` }));
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/global/Navigation.astro", void 0);

const $$Wrapper = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Wrapper;
  const { variant = "standard", class: extraClass = "" } = Astro2.props;
  const variantClasses = {
    // Narrow
    narrow: "max-w-2xl  mx-auto px-4",
    // Standard wrapper
    standard: "px-8 mx-auto md:px-12 max-w-screen 2xl:max-w-[1440px]",
    // Paddingless Desktop
    paddinglessDesktop: "mx-auto max-w-6xl px-4 xl:px-0 overflow-hidden xl:overflow-visible",
    // Prose styles
    prose: "prose text-zinc-900 prose-blockquote:border-l-accent prose-a:border-white prose-a:border-b prose-a:no-underline prose-a:text-white prose-a:transition-colors prose-a:duration-200 prose-a:hover:border-solid prose-a:hover:text-accent-500 prose-headings:font-medium prose-headings:text-white prose-pre:border prose-li:marker:text-accent-400 max-w-none prose-pre:rounded-xl w-full prose-blockquote:text-base-500 prose-pre:border-base-300 prose-ul:[list-style-type:'///'] prose-pre:scrollbar-hide prose-tr:border-base-800 prose-thead:border-base-800 prose-strong:text-white"
  };
  const classes = `${variantClasses[variant]} ${extraClass}`.trim();
  return renderTemplate`${maybeRenderHead()}<div${addAttribute(classes, "class")}> ${renderSlot($$result, $$slots["default"])} </div>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/containers/Wrapper.astro", void 0);

var __freeze$1 = Object.freeze;
var __defProp$1 = Object.defineProperty;
var __template$1 = (cooked, raw) => __freeze$1(__defProp$1(cooked, "raw", { value: __freeze$1(raw || cooked.slice()) }));
var _a$1;
createComponent(($$result, $$props, $$slots) => {
  const navigationLinks = config.menu_global || [];
  return renderTemplate(_a$1 || (_a$1 = __template$1(["", '<div id="nav-wrapper" class="fixed inset-x-0 top-0 z-50 w-full mx-auto bg-white border-b border-dashed border-base-200"> ', ' </div> <script type="module">\n  document.addEventListener("DOMContentLoaded", () => {\n    const menuToggle = document.getElementById("menu-toggle");\n    const menuClose = document.getElementById("menu-close");\n    const menuIcon = document.getElementById("menu-icon");\n    const closeIcon = document.getElementById("close-icon");\n    const navigationMenu = document.getElementById("navigation-menu");\n    // Toggle mobile menu\n    function toggleMenu(open) {\n      console.log(`Toggling menu. Open: ${open}`);\n      navigationMenu.classList.toggle("opacity-100", open);\n      navigationMenu.classList.toggle("translate-y-0", open);\n      navigationMenu.classList.toggle("pointer-events-auto", open);\n      navigationMenu.classList.toggle("opacity-0", !open);\n      navigationMenu.classList.toggle("-translate-y-4", !open);\n      navigationMenu.classList.toggle("pointer-events-none", !open);\n      menuIcon.classList.toggle("hidden", open);\n      closeIcon.classList.toggle("hidden", !open);\n    }\n    // Event Listeners\n    if(menuToggle) menuToggle.addEventListener("click", () => toggleMenu(true));\n    if(menuClose) menuClose.addEventListener("click", () => toggleMenu(false));\n  });\n<\/script>'], ["", '<div id="nav-wrapper" class="fixed inset-x-0 top-0 z-50 w-full mx-auto bg-white border-b border-dashed border-base-200"> ', ' </div> <script type="module">\n  document.addEventListener("DOMContentLoaded", () => {\n    const menuToggle = document.getElementById("menu-toggle");\n    const menuClose = document.getElementById("menu-close");\n    const menuIcon = document.getElementById("menu-icon");\n    const closeIcon = document.getElementById("close-icon");\n    const navigationMenu = document.getElementById("navigation-menu");\n    // Toggle mobile menu\n    function toggleMenu(open) {\n      console.log(\\`Toggling menu. Open: \\${open}\\`);\n      navigationMenu.classList.toggle("opacity-100", open);\n      navigationMenu.classList.toggle("translate-y-0", open);\n      navigationMenu.classList.toggle("pointer-events-auto", open);\n      navigationMenu.classList.toggle("opacity-0", !open);\n      navigationMenu.classList.toggle("-translate-y-4", !open);\n      navigationMenu.classList.toggle("pointer-events-none", !open);\n      menuIcon.classList.toggle("hidden", open);\n      closeIcon.classList.toggle("hidden", !open);\n    }\n    // Event Listeners\n    if(menuToggle) menuToggle.addEventListener("click", () => toggleMenu(true));\n    if(menuClose) menuClose.addEventListener("click", () => toggleMenu(false));\n  });\n<\/script>'])), maybeRenderHead(), renderComponent($$result, "Wrapper", $$Wrapper, { "id": "second-wrapper", "variant": "standard", "class": "py-4" }, { "default": ($$result2) => renderTemplate` <div id="navigation-wrapper" class="relative flex flex-col md:items-center md:justify-between md:flex-row"> <div class="flex flex-row items-center justify-between"> <a href="/"> <span class="sr-only">Ir al inicio</span> ${renderComponent($$result2, "Logo", $$Logo, { "class": "h-6 text-base-800" })} </a> <button id="menu-toggle" class="inline-flex items-center justify-center p-2 text-base-600 hover:text-base-800 focus:outline-none focus:text-base-500 md:hidden"> <svg class="size-6" stroke="currentColor" fill="none" viewBox="0 0 24 24"> <path id="menu-icon" class="inline-flex" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path> <path id="close-icon" class="hidden" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path> </svg> </button> </div> <nav id="navigation-menu" class="fixed inset-0 flex flex-col justify-between h-full py-12 bg-white opacity-0 pointer-events-none md:bg-none md:bg-transparent lg:p-0 md:p-0 transform transition-all duration-300 ease-in-out -translate-y-4 md:relative md:inset-auto md:opacity-100 md:pointer-events-auto md:translate-y-0"> <div class="absolute inset-0 mx-2 pointer-events-none bg-sand-50 border-x border-base-200 md:hidden"></div> <button id="menu-close" class="absolute top-4 right-4 md:hidden focus:outline-none text-base-800" aria-label="Close menu"> <svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"> <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path> </svg> </button> <div class="relative flex flex-col items-start justify-start w-full h-full px-8 list-none md:ml-auto gap-12 md:px-0 md:flex-row md:items-center md:justify-center md:text-left md:gap-4"> <a href="/" class="md:hidden"> <span class="sr-only">Ir al inicio</span> ${renderComponent($$result2, "Logo", $$Logo, { "class": "h-12 text-base-800" })} </a> <div class="flex flex-col gap-2 md:gap-4 md:flex-row"> ${navigationLinks.map((link) => renderTemplate`<a${addAttribute(link.ruta, "href")} class=" text-2xl md:text-sm  hover:text-base-600 text-base-500"> ${link.nombre} </a>`)} </div> <div class="flex flex-wrap items-center mt-auto gap-2"> ${renderComponent($$result2, "Button", $$Button, { "isLink": true, "size": "md", "variant": "muted", "href": "/" }, { "default": ($$result3) => renderTemplate`
Comenzar
` })} ${renderComponent($$result2, "Button", $$Button, { "isLink": true, "size": "md", "variant": "accent", "href": "/" }, { "default": ($$result3) => renderTemplate`
Contacto
` })} </div> </div> </nav> </div> ` }));
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/global/NavigationV2.astro", void 0);

const $$X = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$X;
  const { size = "md" } = Astro2.props;
  const sizes = {
    sm: "size-4",
    md: "size-6",
    lg: "size-8"
  };
  const sizeClass = sizes[size] || sizes.md;
  return renderTemplate`${maybeRenderHead()}<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"${addAttribute(sizeClass, "class")}> <path d="M18 6 6 18"></path> <path d="m6 6 12 12"></path> </svg>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/icons/X.astro", void 0);

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(cooked.slice()) }));
var _a;
createComponent(($$result, $$props, $$slots) => {
  const navigationLinks = config.menu_global || [];
  return renderTemplate(_a || (_a = __template(["", '<div id="nav-wrapper" class="fixed inset-x-0 top-0 w-full mx-auto z-51 bg-base-950"> ', ' </div> <script type="module">\n  document.addEventListener("DOMContentLoaded", () => {\n    const menuToggle = document.getElementById("menu-toggle");\n    const menuClose = document.getElementById("menu-close");\n    const menuIcon = document.getElementById("menu-icon");\n    const closeIcon = document.getElementById("close-icon");\n    const navigationMenu = document.getElementById("navigation-menu");\n    // Toggle mobile menu\n    function toggleMenu(open) {\n      if(!navigationMenu) return;\n      navigationMenu.classList.toggle("opacity-100", open);\n      navigationMenu.classList.toggle("translate-y-0", open);\n      navigationMenu.classList.toggle("pointer-events-auto", open);\n      navigationMenu.classList.toggle("opacity-0", !open);\n      navigationMenu.classList.toggle("-translate-y-4", !open);\n      navigationMenu.classList.toggle("pointer-events-none", !open);\n      if(menuIcon) menuIcon.classList.toggle("hidden", open);\n      if(closeIcon) closeIcon.classList.toggle("hidden", !open);\n    }\n    // Event Listeners\n    if(menuToggle) menuToggle.addEventListener("click", () => toggleMenu(true));\n    if(menuClose) menuClose.addEventListener("click", () => toggleMenu(false));\n  });\n<\/script>'])), maybeRenderHead(), renderComponent($$result, "Wrapper", $$Wrapper, { "id": "second-wrapper", "variant": "paddinglessDesktop", "class": "py-4 border-b lg:py-8 border-base-800" }, { "default": ($$result2) => renderTemplate` <div id="navigation-wrapper" class="relative flex flex-col md:items-center md:justify-start md:gap-12 md:flex-row"> <div class="flex flex-row items-center justify-between"> <a href="/" class="flex items-center text-xs text-white gap-2"> <span class="sr-only">Ir al inicio</span> ${renderComponent($$result2, "Logo", $$Logo, { "class": "h-8" })} <span class="font-bold text-lg">${config.nombre_sitio}</span> </a> ${renderComponent($$result2, "Button", $$Button, { "id": "menu-toggle", "size": "md", "variant": "muted", "class": "md:hidden" }, { "default": ($$result3) => renderTemplate` <svg class="size-4" stroke="currentColor" fill="none" viewBox="0 0 24 24"> <path id="menu-icon" class="inline-flex" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path> <path id="close-icon" class="hidden" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path> </svg> ` })} </div> <nav id="navigation-menu" class="fixed inset-0 flex flex-col justify-between h-full py-12 bg-black opacity-0 pointer-events-none md:bg-none md:bg-transparent lg:p-0 md:p-0 transform transition-all duration-300 ease-in-out -translate-y-4 md:relative md:inset-auto md:opacity-100 md:pointer-events-auto md:translate-y-0 md:w-full"> <button id="menu-close" class="absolute top-4 right-4 md:hidden focus:outline-none text-white p-2" aria-label="Close menu"> ${renderComponent($$result2, "X", $$X, { "size": "sm" })} </button> <div class="relative flex flex-col items-start justify-start w-full h-full px-8 py-12 md:py-0 gap-12 md:px-0 md:flex-row md:items-center md:text-left overflow-hidden lg:overflow-visible"> <div aria-hidden="true" class="block md:hidden absolute inset-0 pointer-events-none my-12 bg-accent-vertical-stripes w-[10%] ml-auto"></div> <a href="/" class="md:hidden"> <span class="sr-only">Ir al inicio</span> ${renderComponent($$result2, "Logo", $$Logo, { "class": "h-12 text-white" })} </a> <div class="relative flex flex-col gap-2 md:gap-4 md:flex-row md:mr-auto"> ${navigationLinks.map((link) => renderTemplate`<a${addAttribute(link.ruta, "href")} class="text-2xl text-white md:text-xs hover:text-accent-400"> ${link.nombre} </a>`)} </div> <div class="flex flex-wrap items-center mt-auto gap-2"> ${renderComponent($$result2, "Button", $$Button, { "isLink": true, "size": "md", "variant": "muted", "href": "/" }, { "default": ($$result3) => renderTemplate`
Comenzar
` })} </div> </div> </nav> </div> ` }));
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/global/NavigationV3.astro", void 0);

const $$Text = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Text;
  const textStyles = {
    display6XL: "text-4xl sm:text-7xl md:text-9xl lg:text-[12rem]",
    display5XL: "text-4xl sm:text-7xl md:text-8xl lg:text-[10rem]",
    display4XL: "text-4xl sm:text-7xl md:text-8xl lg:text-9xl",
    display3XL: "text-5xl sm:text-6xl md:text-7xl lg:text-8xl",
    display2XL: "text-5xl sm:text-5xl md:text-6xl lg:text-7xl",
    displayXL: "text-4xl sm:text-4xl md:text-5xl lg:text-6xl",
    displayLG: "text-3xl sm:text-3xl md:text-4xl lg:text-5xl",
    displayMD: "text-2xl md:text-3xl lg:text-4xl",
    displaySM: "text-xl md:text-2xl lg:text-3xl",
    displayXS: "text-xl lg:text-2xl",
    textXL: "text-xl md:text-2xl",
    textLG: "text-lg md:text-xl ",
    textBase: "text-base",
    textSM: "text-sm ",
    textXS: "text-xs "
  };
  const {
    tag: Tag = "p",
    // Defaults to paragraph tag
    class: className = "",
    // No additional classes by default
    variant,
    // No default variant
    ...rest
    // Collect remaining props
  } = Astro2.props;
  const baseClasses = variant ? textStyles[variant] || textStyles.textBase : "";
  const combinedClasses = `${baseClasses} ${className}`.trim();
  return renderTemplate`${renderComponent($$result, "Tag", Tag, { "class": combinedClasses, ...rest }, { "default": ($$result2) => renderTemplate` ${renderSlot($$result2, $$slots["left-icon"])} ${renderSlot($$result2, $$slots["default"])} ${renderSlot($$result2, $$slots["right-icon"])} ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/elements/Text.astro", void 0);

const $$Footer = createComponent(($$result, $$props, $$slots) => {
  const footerLinks = [
    {
      title: "Explora",
      links: config.menu_global || []
    }
  ];
  const anioActual = (/* @__PURE__ */ new Date()).getFullYear();
  return renderTemplate`${maybeRenderHead()}<footer class="relative mt-20"> ${renderComponent($$result, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-8" }, { "default": ($$result2) => renderTemplate` <div class="items-start pt-12 mt-12 tracking-tight border-t grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-24 border-base-200"> <div class="items-start tracking-tight grid grid-cols-2 gap-x-8 gap-y-12"> ${footerLinks.map((section) => renderTemplate`<div> ${renderComponent($$result2, "Text", $$Text, { "tag": "h3", "variant": "textBase", "class": "font-medium text-base-600" }, { "default": ($$result3) => renderTemplate`${section.title}` })} <ul role="list" class="mt-4 space-y-2"> ${section.links.map((link) => renderTemplate`<li> <a class="text-base-500  hover:text-base-800"${addAttribute(link.ruta, "href")}> ${link.nombre} </a> </li>`)} </ul> </div>`)} <div> ${renderComponent($$result2, "Text", $$Text, { "tag": "h3", "variant": "textBase", "class": "font-medium text-base-600" }, { "default": ($$result3) => renderTemplate`
Legal
` })} <ul role="list" class="mt-4 space-y-2"> <li><a class="text-base-500 hover:text-base-800" href="/politica-de-privacidad">Privacidad</a></li> <li><a class="text-base-500 hover:text-base-800" href="/terminos">Términos</a></li> </ul> </div> </div> <div class="flex flex-col justify-between h-full p-8 bg-base-50"> ${renderComponent($$result2, "Text", $$Text, { "tag": "p", "variant": "displaySM", "class": "md:max-w-sm text-base-800 text-balance font-medium" }, { "default": ($$result3) => renderTemplate`${config.nombre_sitio}` })} ${renderComponent($$result2, "Text", $$Text, { "tag": "p", "variant": "textSM", "class": "text-base-500 mt-2" }, { "default": ($$result3) => renderTemplate`${config.seo.descripcion_base}` })} <div class="mt-8"> ${renderComponent($$result2, "Text", $$Text, { "tag": "p", "variant": "textXS", "class": "text-base-500" }, { "default": ($$result3) => renderTemplate`
© ${anioActual}${config.footer.empresa_legal}. ${config.footer.direccion}` })} ${renderComponent($$result2, "Text", $$Text, { "tag": "p", "variant": "textXS", "class": "text-base-500 mt-1" }, { "default": ($$result3) => renderTemplate`${config.footer.email_contacto}` })} </div> </div> </div> ` })} </footer>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/global/Footer.astro", void 0);

createComponent(($$result, $$props, $$slots) => {
  const footerLinks = [
    {
      heading: "Enlaces",
      links: config.menu_global || []
    },
    {
      heading: "Legal",
      links: [
        { label: "Privacidad", href: "/politica-de-privacidad" },
        { label: "Términos", href: "/terminos" }
      ]
    }
  ];
  const anioActual = (/* @__PURE__ */ new Date()).getFullYear();
  return renderTemplate`${maybeRenderHead()}<footer class="border-t border-base-200 border-dashed"> ${renderComponent($$result, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-12" }, { "default": ($$result2) => renderTemplate` <div class="xl:grid xl:grid-cols-3 xl:gap-8"> <div class="text-black"> <a href="/" class="flex items-center font-serif text-lg gap-2 text-accent-900"> <span class="sr-only">Ir al inicio</span> ${renderComponent($$result2, "Logo", $$Logo, { "class": "h-4 text-base-900" })} ${config.nombre_sitio} </a> <p class="mt-1 text-sm font-normal text-base-500 text-balance"> ${config.seo.descripcion_base} </p> </div> <div class="md:grid md:grid-cols-2 xl:grid-cols-4 md:gap-8 xl:col-span-2"> ${footerLinks.map((section) => renderTemplate`<div class="mt-12 md:mt-0"> <h3 class="text-black font-display font-bold">${section.heading}</h3> <ul role="list" class="mt-4 text-sm space-y-2 text-base-500"> ${section.links.map((link) => renderTemplate`<li> <a${addAttribute(link.href || link.ruta, "href")} class="hover:text-black"> ${link.label || link.nombre} </a> </li>`)} </ul> </div>`)} </div> </div> <div class="mt-8 pt-8 border-t border-base-200 border-dashed text-xs text-base-400">
© ${anioActual} ${config.footer.empresa_legal}. ${config.footer.direccion} </div> ` })} </footer>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/global/FooterV2.astro", void 0);

createComponent(($$result, $$props, $$slots) => {
  const footerLinks = [
    {
      heading: "Enlaces",
      links: config.menu_global || []
    },
    {
      heading: "Legal",
      links: [
        { label: "Privacidad", href: "/politica-de-privacidad" },
        { label: "Términos", href: "/terminos" }
      ]
    }
  ];
  return renderTemplate`${maybeRenderHead()}<footer class="bg-base-950"> ${renderComponent($$result, "Wrapper", $$Wrapper, { "variant": "paddinglessDesktop", "class": "relative py-12 overflow-hidden border-white/10 border-t" }, { "default": ($$result2) => renderTemplate` <div class="relative pb-24 gap-8 grid grid-cols-1 lg:grid-cols-3"> <div class="text-white"> <a href="/" class="flex items-center text-sm text-white gap-2"> <span class="sr-only">Ir al inicio</span> ${renderComponent($$result2, "Logo", $$Logo, { "class": "h-6" })} <span class="font-bold text-lg">${config.nombre_sitio}</span> </a> <p class="mt-1 text-sm font-normal text-base-500 text-balance"> ${config.seo.descripcion_base} </p> </div> <div class="grid grid-cols-2 gap-8 xl:col-span-2 xl:col-start-3"> ${footerLinks.map((section) => renderTemplate`<div> ${renderComponent($$result2, "Text", $$Text, { "tag": "h3", "variant": "textBase", "class": "text-white font-display font-bold" }, { "default": ($$result3) => renderTemplate`${section.heading}` })} <ul role="list" class="mt-2 text-sm space-y-1 text-base-500"> ${section.links.map((link) => renderTemplate`<li> <a${addAttribute(link.href || link.ruta, "href")} class="hover:text-white transition-colors"> ${link.label || link.nombre} </a> </li>`)} </ul> </div>`)} </div> </div> <div aria-hidden="true" class="bg-light-vertical-stripes p-20 clip-rect-inset lg:py-62 mt-12 opacity-5"></div> <div class="mt-12 text-xs text-base-500 border-t border-white/5 pt-8">
© ${(/* @__PURE__ */ new Date()).getFullYear()} ${config.footer.empresa_legal}. ${config.footer.direccion} </div> ` })} </footer>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/global/FooterV3.astro", void 0);

const $$BaseLayout = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$BaseLayout;
  const { titulo, descripcion, hideNav = false, hideFooter = false } = Astro2.props;
  const fontName = config.font_family;
  const palette = config.color_palette || {
    primary: "#000000",
    secondary: "#4b5563",
    accent: "#2563eb",
    text_bold: "#000000"
  };
  let SelectedNav = $$Navigation;
  let SelectedFooter = $$Footer;
  const $$definedVars = defineStyleVars([{
    primary: palette.primary,
    secondary: palette.secondary,
    accent: palette.accent,
    textBold: palette.text_bold
  }]);
  return renderTemplate`<html lang="es" class="scroll-smooth selection:bg-sand-100 selection:text-accent-500" data-astro-cid-37fxchfa${addAttribute($$definedVars, "style")}> <head>${renderComponent($$result, "BaseHead", $$BaseHead, { "titulo": titulo, "descripcion": descripcion, "data-astro-cid-37fxchfa": true })}${renderHead()}</head> <body class="relative flex flex-col bg-white min-h-dvh"${addAttribute(`${`font-family: '${fontName}', sans-serif;`}; ${$$definedVars}`, "style")} data-astro-cid-37fxchfa> ${!hideNav && renderTemplate`${renderComponent($$result, "SelectedNav", SelectedNav, { "data-astro-cid-37fxchfa": true })}`} <main class="flex-grow pt-24" data-astro-cid-37fxchfa${addAttribute($$definedVars, "style")}>${renderSlot($$result, $$slots["default"])}</main> ${!hideFooter && renderTemplate`${renderComponent($$result, "SelectedFooter", SelectedFooter, { "data-astro-cid-37fxchfa": true })}`} </body></html>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/BaseLayout.astro", void 0);

const $$LayoutA = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutA;
  const { titulo, descripcion } = Astro2.props;
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-12" }, { "default": ($$result3) => renderTemplate` ${renderSlot($$result3, $$slots["default"])} ` })} ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutA.astro", void 0);

const $$LayoutB = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutB;
  const { titulo, descripcion } = Astro2.props;
  const sidebarPos = config.sidebar_pos || "right";
  const menuItems = config.menu_global || [];
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-12" }, { "default": ($$result3) => renderTemplate` ${maybeRenderHead()}<div${addAttribute(`flex flex-col lg:flex-row gap-12 ${sidebarPos === "left" ? "lg:flex-row-reverse" : ""}`, "class")}> <main class="lg:w-2/3"> ${renderSlot($$result3, $$slots["default"])} </main> <aside class="lg:w-1/3"> <div class="bg-zinc-50 p-8 outline outline-base-200"> ${renderComponent($$result3, "Text", $$Text, { "tag": "h3", "variant": "textLG", "class": "font-bold text-black mb-4" }, { "default": ($$result4) => renderTemplate`📌 Enlaces Rápidos` })} <ul class="space-y-3"> ${menuItems.map((item) => renderTemplate`<li><a${addAttribute(item.ruta, "href")} class="text-zinc-600 hover:text-black transition-colors">${item.nombre}</a></li>`)} </ul> <div class="mt-8 pt-8 border-t border-base-200"> ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textSM", "class": "text-zinc-500 italic" }, { "default": ($$result4) => renderTemplate`${config.seo.descripcion_base}` })} </div> </div> </aside> </div> ` })} ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutB.astro", void 0);

const $$LayoutC = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutC;
  const { titulo, descripcion } = Astro2.props;
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-12 flex justify-center" }, { "default": ($$result3) => renderTemplate` ${maybeRenderHead()}<div class="w-full max-w-3xl"> <main class="bg-white p-10 outline outline-base-200 shadow-sm border-t-8 border-[var(--color-primary)]"> ${renderSlot($$result3, $$slots["default"])} </main> </div> ` })} ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutC.astro", void 0);

const VALID_SUPPORTED_FORMATS = [
  "jpeg",
  "jpg",
  "png",
  "tiff",
  "webp",
  "gif",
  "svg",
  "avif"
];
const DEFAULT_OUTPUT_FORMAT = "webp";
const DEFAULT_HASH_PROPS = [
  "src",
  "width",
  "height",
  "format",
  "quality",
  "fit",
  "position",
  "background"
];

const DEFAULT_RESOLUTIONS = [
  640,
  // older and lower-end phones
  750,
  // iPhone 6-8
  828,
  // iPhone XR/11
  960,
  // older horizontal phones
  1080,
  // iPhone 6-8 Plus
  1280,
  // 720p
  1668,
  // Various iPads
  1920,
  // 1080p
  2048,
  // QXGA
  2560,
  // WQXGA
  3200,
  // QHD+
  3840,
  // 4K
  4480,
  // 4.5K
  5120,
  // 5K
  6016
  // 6K
];
const LIMITED_RESOLUTIONS = [
  640,
  // older and lower-end phones
  750,
  // iPhone 6-8
  828,
  // iPhone XR/11
  1080,
  // iPhone 6-8 Plus
  1280,
  // 720p
  1668,
  // Various iPads
  2048,
  // QXGA
  2560
  // WQXGA
];
const getWidths = ({
  width,
  layout,
  breakpoints = DEFAULT_RESOLUTIONS,
  originalWidth
}) => {
  const smallerThanOriginal = (w) => !originalWidth || w <= originalWidth;
  if (layout === "full-width") {
    return breakpoints.filter(smallerThanOriginal);
  }
  if (!width) {
    return [];
  }
  const doubleWidth = width * 2;
  const maxSize = originalWidth ? Math.min(doubleWidth, originalWidth) : doubleWidth;
  if (layout === "fixed") {
    return originalWidth && width > originalWidth ? [originalWidth] : [width, maxSize];
  }
  if (layout === "constrained") {
    return [
      // Always include the image at 1x and 2x the specified width
      width,
      doubleWidth,
      ...breakpoints
    ].filter((w) => w <= maxSize).sort((a, b) => a - b);
  }
  return [];
};
const getSizesAttribute = ({
  width,
  layout
}) => {
  if (!width || !layout) {
    return void 0;
  }
  switch (layout) {
    // If screen is wider than the max size then image width is the max size,
    // otherwise it's the width of the screen
    case "constrained":
      return `(min-width: ${width}px) ${width}px, 100vw`;
    // Image is always the same width, whatever the size of the screen
    case "fixed":
      return `${width}px`;
    // Image is always the width of the screen
    case "full-width":
      return `100vw`;
    case "none":
    default:
      return void 0;
  }
};

function isLocalService(service) {
  if (!service) {
    return false;
  }
  return "transform" in service;
}
function parseQuality(quality) {
  let result = Number.parseInt(quality);
  if (Number.isNaN(result)) {
    return quality;
  }
  return result;
}
const sortNumeric = (a, b) => a - b;
function verifyOptions(options) {
  if (!options.src || !isRemoteImage(options.src) && !isESMImportedImage(options.src)) {
    throw new AstroError({
      ...ExpectedImage,
      message: ExpectedImage.message(
        JSON.stringify(options.src),
        typeof options.src,
        JSON.stringify(options, (_, v) => v === void 0 ? null : v)
      )
    });
  }
  if (!isESMImportedImage(options.src)) {
    if (options.src.startsWith("/@fs/") || !isRemotePath(options.src) && !options.src.startsWith("/")) {
      throw new AstroError({
        ...LocalImageUsedWrongly,
        message: LocalImageUsedWrongly.message(options.src)
      });
    }
    let missingDimension;
    if (!options.width && !options.height) {
      missingDimension = "both";
    } else if (!options.width && options.height) {
      missingDimension = "width";
    } else if (options.width && !options.height) {
      missingDimension = "height";
    }
    if (missingDimension) {
      throw new AstroError({
        ...MissingImageDimension,
        message: MissingImageDimension.message(missingDimension, options.src)
      });
    }
  } else {
    if (!VALID_SUPPORTED_FORMATS.includes(options.src.format)) {
      throw new AstroError({
        ...UnsupportedImageFormat,
        message: UnsupportedImageFormat.message(
          options.src.format,
          options.src.src,
          VALID_SUPPORTED_FORMATS
        )
      });
    }
    if (options.widths && options.densities) {
      throw new AstroError(IncompatibleDescriptorOptions);
    }
    if (options.src.format !== "svg" && options.format === "svg") {
      throw new AstroError(UnsupportedImageConversion);
    }
  }
}
const baseService = {
  validateOptions(options) {
    verifyOptions(options);
    if (!options.format) {
      if (isESMImportedImage(options.src) && options.src.format === "svg") {
        options.format = "svg";
      } else {
        options.format = DEFAULT_OUTPUT_FORMAT;
      }
    }
    if (options.width) options.width = Math.round(options.width);
    if (options.height) options.height = Math.round(options.height);
    if (options.layout) {
      delete options.layout;
    }
    if (options.fit === "none") {
      delete options.fit;
    }
    return options;
  },
  getHTMLAttributes(options) {
    const { targetWidth, targetHeight } = getTargetDimensions(options);
    const {
      src,
      width,
      height,
      format,
      quality,
      densities,
      widths,
      formats,
      layout,
      priority,
      fit,
      position,
      background,
      ...attributes
    } = options;
    return {
      ...attributes,
      width: targetWidth,
      height: targetHeight,
      loading: attributes.loading ?? "lazy",
      decoding: attributes.decoding ?? "async"
    };
  },
  getSrcSet(options) {
    const { targetWidth, targetHeight } = getTargetDimensions(options);
    const aspectRatio = targetWidth / targetHeight;
    const { widths, densities } = options;
    const targetFormat = options.format ?? DEFAULT_OUTPUT_FORMAT;
    let transformedWidths = (widths ?? []).sort(sortNumeric);
    let imageWidth = options.width;
    let maxWidth = Number.POSITIVE_INFINITY;
    if (isESMImportedImage(options.src)) {
      imageWidth = options.src.width;
      maxWidth = imageWidth;
      if (transformedWidths.length > 0 && transformedWidths.at(-1) > maxWidth) {
        transformedWidths = transformedWidths.filter((width) => width <= maxWidth);
        transformedWidths.push(maxWidth);
      }
    }
    transformedWidths = Array.from(new Set(transformedWidths));
    const {
      width: transformWidth,
      height: transformHeight,
      ...transformWithoutDimensions
    } = options;
    let allWidths = [];
    if (densities) {
      const densityValues = densities.map((density) => {
        if (typeof density === "number") {
          return density;
        } else {
          return Number.parseFloat(density);
        }
      });
      const densityWidths = densityValues.sort(sortNumeric).map((density) => Math.round(targetWidth * density));
      allWidths = densityWidths.map((width, index) => ({
        width,
        descriptor: `${densityValues[index]}x`
      }));
    } else if (transformedWidths.length > 0) {
      allWidths = transformedWidths.map((width) => ({
        width,
        descriptor: `${width}w`
      }));
    }
    return allWidths.map(({ width, descriptor }) => {
      const height = Math.round(width / aspectRatio);
      const transform = { ...transformWithoutDimensions, width, height };
      return {
        transform,
        descriptor,
        attributes: {
          type: `image/${targetFormat}`
        }
      };
    });
  },
  getURL(options, imageConfig) {
    const searchParams = new URLSearchParams();
    if (isESMImportedImage(options.src)) {
      searchParams.append("href", options.src.src);
    } else if (isRemoteAllowed(options.src, imageConfig)) {
      searchParams.append("href", options.src);
    } else {
      return options.src;
    }
    const params = {
      w: "width",
      h: "height",
      q: "quality",
      f: "format",
      fit: "fit",
      position: "position",
      background: "background"
    };
    Object.entries(params).forEach(([param, key]) => {
      options[key] && searchParams.append(param, options[key].toString());
    });
    const imageEndpoint = joinPaths("/", imageConfig.endpoint.route);
    let url = `${imageEndpoint}?${searchParams}`;
    if (imageConfig.assetQueryParams) {
      const assetQueryString = imageConfig.assetQueryParams.toString();
      if (assetQueryString) {
        url += "&" + assetQueryString;
      }
    }
    return url;
  },
  parseURL(url) {
    const params = url.searchParams;
    if (!params.has("href")) {
      return void 0;
    }
    const transform = {
      src: params.get("href"),
      width: params.has("w") ? Number.parseInt(params.get("w")) : void 0,
      height: params.has("h") ? Number.parseInt(params.get("h")) : void 0,
      format: params.get("f"),
      quality: params.get("q"),
      fit: params.get("fit"),
      position: params.get("position") ?? void 0,
      background: params.get("background") ?? void 0
    };
    return transform;
  },
  getRemoteSize(url, imageConfig) {
    return inferRemoteSize(url, imageConfig);
  }
};
function getTargetDimensions(options) {
  let targetWidth = options.width;
  let targetHeight = options.height;
  if (isESMImportedImage(options.src)) {
    const aspectRatio = options.src.width / options.src.height;
    if (targetHeight && !targetWidth) {
      targetWidth = Math.round(targetHeight * aspectRatio);
    } else if (targetWidth && !targetHeight) {
      targetHeight = Math.round(targetWidth / aspectRatio);
    } else if (!targetWidth && !targetHeight) {
      targetWidth = options.src.width;
      targetHeight = options.src.height;
    }
  }
  return {
    targetWidth,
    targetHeight
  };
}

function isImageMetadata(src) {
  return src.fsPath && !("fsPath" in src);
}

const PLACEHOLDER_BASE = "astro://placeholder";
function createPlaceholderURL(pathOrUrl) {
  return new URL(pathOrUrl, PLACEHOLDER_BASE);
}
function stringifyPlaceholderURL(url) {
  return url.href.replace(PLACEHOLDER_BASE, "");
}

const cssFitValues = ["fill", "contain", "cover", "scale-down"];
async function getConfiguredImageService() {
  if (!globalThis?.astroAsset?.imageService) {
    const { default: service } = await import(
      // @ts-expect-error
      './sharp_9Ebs60t7.mjs'
    ).catch((e) => {
      const error = new AstroError(InvalidImageService);
      error.cause = e;
      throw error;
    });
    if (!globalThis.astroAsset) globalThis.astroAsset = {};
    globalThis.astroAsset.imageService = service;
    return service;
  }
  return globalThis.astroAsset.imageService;
}
async function getImage$1(options, imageConfig) {
  if (!options || typeof options !== "object") {
    throw new AstroError({
      ...ExpectedImageOptions,
      message: ExpectedImageOptions.message(JSON.stringify(options))
    });
  }
  if (typeof options.src === "undefined") {
    throw new AstroError({
      ...ExpectedImage,
      message: ExpectedImage.message(
        options.src,
        "undefined",
        JSON.stringify(options)
      )
    });
  }
  if (isImageMetadata(options)) {
    throw new AstroError(ExpectedNotESMImage);
  }
  const service = await getConfiguredImageService();
  const resolvedOptions = {
    ...options,
    src: await resolveSrc(options.src)
  };
  let originalWidth;
  let originalHeight;
  if (resolvedOptions.inferSize) {
    delete resolvedOptions.inferSize;
    if (isRemoteImage(resolvedOptions.src) && isRemotePath(resolvedOptions.src)) {
      if (!isRemoteAllowed(resolvedOptions.src, imageConfig)) {
        throw new AstroError({
          ...RemoteImageNotAllowed,
          message: RemoteImageNotAllowed.message(resolvedOptions.src)
        });
      }
      const getRemoteSize = (url) => service.getRemoteSize?.(url, imageConfig) ?? inferRemoteSize(url, imageConfig);
      const result = await getRemoteSize(resolvedOptions.src);
      resolvedOptions.width ??= result.width;
      resolvedOptions.height ??= result.height;
      originalWidth = result.width;
      originalHeight = result.height;
    }
  }
  const originalFilePath = isESMImportedImage(resolvedOptions.src) ? resolvedOptions.src.fsPath : void 0;
  const clonedSrc = isESMImportedImage(resolvedOptions.src) ? (
    // @ts-expect-error - clone is a private, hidden prop
    resolvedOptions.src.clone ?? resolvedOptions.src
  ) : resolvedOptions.src;
  if (isESMImportedImage(clonedSrc)) {
    originalWidth = clonedSrc.width;
    originalHeight = clonedSrc.height;
  }
  if (originalWidth && originalHeight) {
    const aspectRatio = originalWidth / originalHeight;
    if (resolvedOptions.height && !resolvedOptions.width) {
      resolvedOptions.width = Math.round(resolvedOptions.height * aspectRatio);
    } else if (resolvedOptions.width && !resolvedOptions.height) {
      resolvedOptions.height = Math.round(resolvedOptions.width / aspectRatio);
    } else if (!resolvedOptions.width && !resolvedOptions.height) {
      resolvedOptions.width = originalWidth;
      resolvedOptions.height = originalHeight;
    }
  }
  resolvedOptions.src = clonedSrc;
  const layout = options.layout ?? imageConfig.layout ?? "none";
  if (resolvedOptions.priority) {
    resolvedOptions.loading ??= "eager";
    resolvedOptions.decoding ??= "sync";
    resolvedOptions.fetchpriority ??= "high";
    delete resolvedOptions.priority;
  } else {
    resolvedOptions.loading ??= "lazy";
    resolvedOptions.decoding ??= "async";
    resolvedOptions.fetchpriority ??= void 0;
  }
  if (layout !== "none") {
    resolvedOptions.widths ||= getWidths({
      width: resolvedOptions.width,
      layout,
      originalWidth,
      breakpoints: imageConfig.breakpoints?.length ? imageConfig.breakpoints : isLocalService(service) ? LIMITED_RESOLUTIONS : DEFAULT_RESOLUTIONS
    });
    resolvedOptions.sizes ||= getSizesAttribute({ width: resolvedOptions.width, layout });
    delete resolvedOptions.densities;
    resolvedOptions["data-astro-image"] = layout;
    if (resolvedOptions.fit && cssFitValues.includes(resolvedOptions.fit)) {
      resolvedOptions["data-astro-image-fit"] = resolvedOptions.fit;
    }
    if (resolvedOptions.position) {
      resolvedOptions["data-astro-image-pos"] = resolvedOptions.position.replace(/\s+/g, "-");
    }
  }
  const validatedOptions = service.validateOptions ? await service.validateOptions(resolvedOptions, imageConfig) : resolvedOptions;
  const srcSetTransforms = service.getSrcSet ? await service.getSrcSet(validatedOptions, imageConfig) : [];
  const lazyImageURLFactory = (getValue) => {
    let cached = null;
    return () => cached ??= getValue();
  };
  const initialImageURL = await service.getURL(validatedOptions, imageConfig);
  let lazyImageURL = lazyImageURLFactory(() => initialImageURL);
  const matchesValidatedTransform = (transform) => transform.width === validatedOptions.width && transform.height === validatedOptions.height && transform.format === validatedOptions.format;
  let srcSets = await Promise.all(
    srcSetTransforms.map(async (srcSet) => {
      return {
        transform: srcSet.transform,
        url: matchesValidatedTransform(srcSet.transform) ? initialImageURL : await service.getURL(srcSet.transform, imageConfig),
        descriptor: srcSet.descriptor,
        attributes: srcSet.attributes
      };
    })
  );
  if (isLocalService(service) && globalThis.astroAsset.addStaticImage && !(isRemoteImage(validatedOptions.src) && initialImageURL === validatedOptions.src)) {
    const propsToHash = service.propertiesToHash ?? DEFAULT_HASH_PROPS;
    lazyImageURL = lazyImageURLFactory(
      () => globalThis.astroAsset.addStaticImage(validatedOptions, propsToHash, originalFilePath)
    );
    srcSets = srcSetTransforms.map((srcSet) => {
      return {
        transform: srcSet.transform,
        url: matchesValidatedTransform(srcSet.transform) ? lazyImageURL() : globalThis.astroAsset.addStaticImage(srcSet.transform, propsToHash, originalFilePath),
        descriptor: srcSet.descriptor,
        attributes: srcSet.attributes
      };
    });
  } else if (imageConfig.assetQueryParams) {
    const imageURLObj = createPlaceholderURL(initialImageURL);
    imageConfig.assetQueryParams.forEach((value, key) => {
      imageURLObj.searchParams.set(key, value);
    });
    lazyImageURL = lazyImageURLFactory(() => stringifyPlaceholderURL(imageURLObj));
    srcSets = srcSets.map((srcSet) => {
      const urlObj = createPlaceholderURL(srcSet.url);
      imageConfig.assetQueryParams.forEach((value, key) => {
        urlObj.searchParams.set(key, value);
      });
      return {
        ...srcSet,
        url: stringifyPlaceholderURL(urlObj)
      };
    });
  }
  return {
    rawOptions: resolvedOptions,
    options: validatedOptions,
    get src() {
      return lazyImageURL();
    },
    srcSet: {
      values: srcSets,
      attribute: srcSets.map((srcSet) => `${srcSet.url} ${srcSet.descriptor}`).join(", ")
    },
    attributes: service.getHTMLAttributes !== void 0 ? await service.getHTMLAttributes(validatedOptions, imageConfig) : {}
  };
}

Function.prototype.toString.call(Object);

const $$Image = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Image;
  const props = Astro2.props;
  if (props.alt === void 0 || props.alt === null) {
    throw new AstroError(ImageMissingAlt);
  }
  if (typeof props.width === "string") {
    props.width = Number.parseInt(props.width);
  }
  if (typeof props.height === "string") {
    props.height = Number.parseInt(props.height);
  }
  const layout = props.layout ?? imageConfig.layout ?? "none";
  if (layout !== "none") {
    props.layout ??= imageConfig.layout;
    props.fit ??= imageConfig.objectFit ?? "cover";
    props.position ??= imageConfig.objectPosition ?? "center";
  } else if (imageConfig.objectFit || imageConfig.objectPosition) {
    props.fit ??= imageConfig.objectFit;
    props.position ??= imageConfig.objectPosition;
  }
  const image = await getImage(props);
  const additionalAttributes = {};
  if (image.srcSet.values.length > 0) {
    additionalAttributes.srcset = image.srcSet.attribute;
  }
  const { class: className, ...attributes } = { ...additionalAttributes, ...image.attributes };
  return renderTemplate`${maybeRenderHead()}<img${addAttribute(image.src, "src")}${spreadAttributes(attributes)}${addAttribute(className, "class")}>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/node_modules/astro/components/Image.astro", void 0);

const $$Picture = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Picture;
  const defaultFormats = ["webp"];
  const defaultFallbackFormat = "png";
  const specialFormatsFallback = ["gif", "svg", "jpg", "jpeg"];
  const { formats = defaultFormats, pictureAttributes = {}, fallbackFormat, ...props } = Astro2.props;
  if (props.alt === void 0 || props.alt === null) {
    throw new AstroError(ImageMissingAlt);
  }
  const scopedStyleClass = props.class?.match(/\bastro-\w{8}\b/)?.[0];
  if (scopedStyleClass) {
    if (pictureAttributes.class) {
      pictureAttributes.class = `${pictureAttributes.class} ${scopedStyleClass}`;
    } else {
      pictureAttributes.class = scopedStyleClass;
    }
  }
  const layout = props.layout ?? imageConfig.layout ?? "none";
  const useResponsive = layout !== "none";
  if (useResponsive) {
    props.layout ??= imageConfig.layout;
    props.fit ??= imageConfig.objectFit ?? "cover";
    props.position ??= imageConfig.objectPosition ?? "center";
  } else if (imageConfig.objectFit || imageConfig.objectPosition) {
    props.fit ??= imageConfig.objectFit;
    props.position ??= imageConfig.objectPosition;
  }
  for (const key in props) {
    if (key.startsWith("data-astro-cid")) {
      pictureAttributes[key] = props[key];
    }
  }
  const originalSrc = await resolveSrc(props.src);
  const optimizedImages = await Promise.all(
    formats.map(
      async (format) => await getImage({
        ...props,
        src: originalSrc,
        format,
        widths: props.widths,
        densities: props.densities
      })
    )
  );
  const clonedSrc = isESMImportedImage(originalSrc) ? (
    // @ts-expect-error - clone is a private, hidden prop
    originalSrc.clone ?? originalSrc
  ) : originalSrc;
  let resultFallbackFormat = fallbackFormat ?? defaultFallbackFormat;
  if (!fallbackFormat && isESMImportedImage(clonedSrc) && specialFormatsFallback.includes(clonedSrc.format)) {
    resultFallbackFormat = clonedSrc.format;
  }
  const fallbackImage = await getImage({
    ...props,
    format: resultFallbackFormat,
    widths: props.widths,
    densities: props.densities
  });
  const imgAdditionalAttributes = {};
  const sourceAdditionalAttributes = {};
  if (props.sizes) {
    sourceAdditionalAttributes.sizes = props.sizes;
  }
  if (fallbackImage.srcSet.values.length > 0) {
    imgAdditionalAttributes.srcset = fallbackImage.srcSet.attribute;
  }
  const { class: className, ...attributes } = {
    ...imgAdditionalAttributes,
    ...fallbackImage.attributes
  };
  return renderTemplate`${maybeRenderHead()}<picture${spreadAttributes(pictureAttributes)}> ${Object.entries(optimizedImages).map(([_, image]) => {
    const srcsetAttribute = props.densities || !props.densities && !props.widths && !useResponsive ? `${image.src}${image.srcSet.values.length > 0 ? ", " + image.srcSet.attribute : ""}` : image.srcSet.attribute;
    return renderTemplate`<source${addAttribute(srcsetAttribute, "srcset")}${addAttribute(mime.lookup(image.options.format ?? image.src) ?? `image/${image.options.format}`, "type")}${spreadAttributes(sourceAdditionalAttributes)}>`;
  })}  <img${addAttribute(fallbackImage.src, "src")}${spreadAttributes(attributes)}${addAttribute(className, "class")}> </picture>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/node_modules/astro/components/Picture.astro", void 0);

const componentDataByCssVariable = new Map([]);

function filterPreloads(data, preload) {
  if (!preload) {
    return null;
  }
  if (preload === true) {
    return data;
  }
  return data.filter(
    ({ weight, style, subset }) => preload.some((p) => {
      if (p.weight !== void 0 && weight !== void 0 && !checkWeight(p.weight.toString(), weight)) {
        return false;
      }
      if (p.style !== void 0 && p.style !== style) {
        return false;
      }
      if (p.subset !== void 0 && p.subset !== subset) {
        return false;
      }
      return true;
    })
  );
}
function checkWeight(input, target) {
  const trimmedInput = input.trim();
  if (trimmedInput.includes(" ")) {
    return trimmedInput === target;
  }
  if (target.includes(" ")) {
    const [a, b] = target.split(" ");
    const parsedInput = Number.parseInt(input);
    return parsedInput >= Number.parseInt(a) && parsedInput <= Number.parseInt(b);
  }
  return input === target;
}

const $$Font = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Font;
  const { cssVariable, preload = false } = Astro2.props;
  const data = componentDataByCssVariable.get(cssVariable);
  if (!data) {
    throw new AstroError({
      ...FontFamilyNotFound,
      message: FontFamilyNotFound.message(cssVariable)
    });
  }
  const filteredPreloadData = filterPreloads(data.preloads, preload);
  return renderTemplate`<style>${unescapeHTML(data.css)}</style>${filteredPreloadData?.map(({ url, type }) => renderTemplate`<link rel="preload"${addAttribute(url, "href")} as="font"${addAttribute(`font/${type}`, "type")} crossorigin>`)}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/node_modules/astro/components/Font.astro", void 0);

const assetQueryParams = undefined;
					const imageConfig = {"endpoint":{"route":"/_image"},"service":{"entrypoint":"astro/assets/services/sharp","config":{}},"domains":[],"remotePatterns":[],"responsiveStyles":false};
					Object.defineProperty(imageConfig, 'assetQueryParams', {
						value: assetQueryParams,
						enumerable: false,
						configurable: true,
					});
							const getImage = async (options) => await getImage$1(options, imageConfig);

const $$LayoutD = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutD;
  const { titulo, descripcion, image } = Astro2.props;
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<section> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "pt-32 pb-4" }, { "default": ($$result3) => renderTemplate` <div class="flex flex-col justify-between max-w-xl mx-auto text-center text-balance"> <div> ${renderComponent($$result3, "Text", $$Text, { "tag": "h1", "variant": "displaySM", "class": "font-serif font-medium tracking-tight text-base-900" }, { "default": ($$result4) => renderTemplate`${titulo}` })} ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textBase", "class": "max-w-xl mx-auto mt-4 text-base-500" }, { "default": ($$result4) => renderTemplate`${descripcion}` })} </div> </div> ${image && renderTemplate`${renderComponent($$result3, "Image", $$Image, { "width": 1e3, "height": 800, "alt": image.alt || titulo, "src": image.url, "class": "object-cover object-center mt-8 size-full max-h-120 lg:col-span-2 rounded-xl" })}`}` })} ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-4 border-t" }, { "default": ($$result3) => renderTemplate` <div class="max-w-xl mx-auto"> ${renderComponent($$result3, "Wrapper", $$Wrapper, { "variant": "prose" }, { "default": ($$result4) => renderTemplate` ${renderSlot($$result4, $$slots["default"])} ` })} </div> ` })} </section> ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutD.astro", void 0);

const $$ChevronRight = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$ChevronRight;
  const { size = "md" } = Astro2.props;
  const sizes = {
    sm: "size-3",
    md: "size-4",
    lg: "size-6"
  };
  const sizeClass = sizes[size] || sizes.md;
  return renderTemplate`${maybeRenderHead()}<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"${addAttribute(sizeClass, "class")}> <path d="m9 18 6-6-6-6"></path> </svg>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/icons/ChevronRight.astro", void 0);

const $$LayoutE = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutE;
  const { titulo, descripcion, image, page = "Blog" } = Astro2.props;
  const breadcrumbs = [
    { label: "Home", href: "/" },
    { label: page, href: "#" }
  ];
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<section> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "pt-32 pb-4" }, { "default": ($$result3) => renderTemplate` <div class="max-w-xl mx-auto text-balance"> <nav aria-label="Breadcrumb" class="bg-sand-100 p-1.5 rounded-full px-6 w-fit"> <ol class="flex items-center text-sm gap-x-2 text-base-600"> ${breadcrumbs.map((item, index) => renderTemplate`${renderComponent($$result3, "Fragment", Fragment, {}, { "default": ($$result4) => renderTemplate` <li> ${index < breadcrumbs.length - 1 ? renderTemplate`<a${addAttribute(item.href, "href")} class="text-xs font-medium hover:text-accent-500 text-base-800"> ${item.label} </a>` : renderTemplate`<span class="text-xs font-medium text-accent-500"> ${item.label} </span>`} </li> ${index < breadcrumbs.length - 1 && renderTemplate`<li class="text-base-400"> ${renderComponent($$result4, "ChevronRight", $$ChevronRight, { "size": "sm" })} </li>`}` })}`)} </ol> </nav> ${renderComponent($$result3, "Text", $$Text, { "tag": "h1", "variant": "displayMD", "class": "mt-12 font-serif font-medium tracking-tight text-black" }, { "default": ($$result4) => renderTemplate`${titulo}` })} ${renderComponent($$result3, "Text", $$Text, { "variant": "textBase", "class": "mt-4 text-base-600" }, { "default": ($$result4) => renderTemplate`
Publicado recientemente
` })} </div> ${image && renderTemplate`${renderComponent($$result3, "Image", $$Image, { "width": 1e3, "height": 800, "alt": image.alt || titulo, "src": image.url, "class": "object-cover object-center mt-8 size-full max-h-120 lg:col-span-2 rounded-xl" })}`}` })} </section> <section> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-12 border-t border-dashed" }, { "default": ($$result3) => renderTemplate` ${renderComponent($$result3, "Wrapper", $$Wrapper, { "variant": "prose", "class": "max-w-xl mx-auto" }, { "default": ($$result4) => renderTemplate` ${renderSlot($$result4, $$slots["default"])} ` })} ` })} </section> ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutE.astro", void 0);

const $$ShareButtons = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$ShareButtons;
  const { description = "" } = Astro2.props;
  return renderTemplate`${maybeRenderHead()}<div class="flex gap-4"> <button class="p-2 bg-sand-100 rounded-full hover:bg-sand-200 transition-colors" aria-label="Share on X"> <svg class="size-4 text-base-800" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"></path></svg> </button> <button class="p-2 bg-sand-100 rounded-full hover:bg-sand-200 transition-colors" aria-label="Share on Facebook"> <svg class="size-4 text-base-800" fill="currentColor" viewBox="0 0 24 24"><path d="M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z"></path></svg> </button> </div>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/fundations/elements/ShareButtons.astro", void 0);

const $$Cross = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$Cross;
  const { class: className } = Astro2.props;
  return renderTemplate`${maybeRenderHead()}<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"${addAttribute(className, "class")}> <path d="M12 2v20"></path> <path d="M2 12h20"></path> </svg>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/assets/Cross.astro", void 0);

const $$LayoutF = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutF;
  const { titulo, descripcion, image } = Astro2.props;
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<section class="overflow-hidden bg-base-950"> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "pt-32 pb-12 relative" }, { "default": ($$result3) => renderTemplate` <div class="flex flex-col justify-between text-center text-balance"> <div> ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textXS", "class": "text-base-500 uppercase tracking-widest" }, { "default": ($$result4) => renderTemplate`
Publicación Destacada
` })} ${renderComponent($$result3, "Text", $$Text, { "tag": "h1", "variant": "displayXL", "class": "tracking-tight text-white font-display mt-8" }, { "default": ($$result4) => renderTemplate`${titulo}` })} ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textBase", "class": "max-w-xl mx-auto mt-4 text-base-400" }, { "default": ($$result4) => renderTemplate`${descripcion}` })} </div> </div> ` })} <div class="aspect-video p-4 bg-accent-500/10 border-y border-white/5 relative flex items-center justify-center"> ${image && renderTemplate`${renderComponent($$result2, "Image", $$Image, { "width": 1200, "height": 600, "src": image.url, "alt": image.alt || titulo, "class": "object-cover w-full h-full max-w-5xl rounded-2xl shadow-dimensional" })}`} </div> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "py-12 border-t border-white/5 overflow-hidden" }, { "default": ($$result3) => renderTemplate` <div class="max-w-xl mx-auto relative px-4"> ${renderComponent($$result3, "Cross", $$Cross, { "class": "absolute -top-[0.6rem] -right-[0.65rem] text-white/20" })} ${renderComponent($$result3, "Cross", $$Cross, { "class": "absolute -top-[0.6rem] -left-[0.65rem] text-white/20" })} ${renderComponent($$result3, "Wrapper", $$Wrapper, { "variant": "prose" }, { "default": ($$result4) => renderTemplate` ${renderSlot($$result4, $$slots["default"])} ` })} <div class="flex flex-wrap mt-12 gap-2 border-t border-white/5 pt-8"> ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textXS", "class": "text-base-500" }, { "default": ($$result4) => renderTemplate`
Compartir artículo:
` })} ${renderComponent($$result3, "ShareButtons", $$ShareButtons, { "description": descripcion })} </div> </div> ` })} </section> ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutF.astro", void 0);

const $$StripesBG = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$StripesBG;
  const { class: className, variant = "base" } = Astro2.props;
  const variants = {
    base: "bg-base-vertical-stripes",
    accent: "bg-accent-vertical-stripes",
    light: "bg-light-vertical-stripes"
  };
  const variantClass = variants[variant] || variants.base;
  return renderTemplate`${maybeRenderHead()}<div aria-hidden="true"${addAttribute(`${variantClass} ${className}`, "class")}></div>`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/components/assets/StripesBG.astro", void 0);

const $$LayoutG = createComponent(($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$props, $$slots);
  Astro2.self = $$LayoutG;
  const { titulo, descripcion, customer = "Cliente", about = "Sobre el proyecto" } = Astro2.props;
  const results = ["Aumento del 200% en tráfico", "Top 1 en keywords objetivo", "ROI positivo en 3 meses"];
  const challenges = [
    { title: "Desafío", content: "Competencia agresiva en el sector salud y requisitos legales estrictos." },
    { title: "Solución", content: "Estrategia de contenido especializado y optimización técnica profunda." }
  ];
  return renderTemplate`${renderComponent($$result, "BaseLayout", $$BaseLayout, { "titulo": titulo, "descripcion": descripcion }, { "default": ($$result2) => renderTemplate` ${maybeRenderHead()}<section class="bg-base-950 text-white"> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard", "class": "relative pt-32 pb-12 overflow-hidden" }, { "default": ($$result3) => renderTemplate` ${renderComponent($$result3, "StripesBG", $$StripesBG, { "variant": "base", "class": "absolute inset-0 h-24 p-20 mt-auto -mx-px border-t border-white/10 opacity-20" })} <div class="max-w-xl mx-auto text-balance relative"> ${renderComponent($$result3, "Text", $$Text, { "tag": "h1", "variant": "displayMD", "class": "text-white font-bold" }, { "default": ($$result4) => renderTemplate`${customer}` })} ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textBase", "class": "mt-4 text-base-300" }, { "default": ($$result4) => renderTemplate`${about}` })} </div> <div class="grid grid-cols-1 md:grid-cols-3 gap-px items-start mt-8 relative border-t border-white/10"> ${results.map((result) => renderTemplate`<div class="gap-2 p-6 pb-24 bg-white/5 h-full border-b border-white"> ${renderComponent($$result3, "Text", $$Text, { "tag": "p", "variant": "textBase", "class": "text-white font-medium" }, { "default": ($$result4) => renderTemplate`${result}` })} </div>`)} </div> ` })} </section> <section class="bg-white py-24"> ${renderComponent($$result2, "Wrapper", $$Wrapper, { "variant": "standard" }, { "default": ($$result3) => renderTemplate` <div class="max-w-3xl mx-auto"> ${renderComponent($$result3, "Wrapper", $$Wrapper, { "variant": "prose", "class": "text-zinc-900" }, { "default": ($$result4) => renderTemplate` ${renderSlot($$result4, $$slots["default"])} ` })} </div> ` })} </section> <section class="bg-base-950"> <dl class="items-center grid grid-cols-1 md:grid-cols-2 gap-px border-t border-white/10"> ${challenges.map((item) => renderTemplate`<div class="flex flex-col h-full overflow-hidden border-r border-white/10 last:border-r-0"> <div class="h-full flex flex-col p-8 pt-24 bg-white/5"> <dt> ${renderComponent($$result2, "Text", $$Text, { "tag": "h3", "variant": "displaySM", "class": "text-white " }, { "default": ($$result3) => renderTemplate`${item.title}` })} </dt> <dd> ${renderComponent($$result2, "Text", $$Text, { "tag": "p", "variant": "textSM", "class": " text-base-300 mt-4" }, { "default": ($$result3) => renderTemplate`${item.content}` })} </dd> </div> <div class="aspect-video p-4 -mx-px bg-accent-vertical-stripes h-full order-first opacity-10"></div> </div>`)} </dl> </section> ` })}`;
}, "/home/elchristog/webpages_interlinking/plantilla_astro_maestra/src/layouts/LayoutG.astro", void 0);

export { $$LayoutA as $, $$LayoutC as a, $$Text as b, createComponent as c, $$Wrapper as d, config as e, $$Button as f, baseService as g, parseQuality as p };
