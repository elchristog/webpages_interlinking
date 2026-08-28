import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const agents = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/agents" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string(),
      intro: z.string(),
      contact: z.array(z.object({ item: z.string() })),
      languages: z.array(z.object({ item: z.string() })),
      stats: z.array(z.object({ key: z.string(), value: z.string() })),
      images: z.array(
        z.object({
          url: z.union([z.string(), image()]),
          alt: z.string(),
        })
      ),
      office: z.string(),
      officeAddress: z.string(),
      avatar: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
    }),
});

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.date(),
  }),
});

const sale = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/sale" }),
  schema: ({ image }) =>
    z.object({
      price: z.string(),
      projectName: z.string(),
      address: z.string(),
      details: z.array(z.object({ key: z.string(), value: z.string() })),
      specs: z.array(z.object({ key: z.string(), value: z.string() })),
      location: z.array(z.object({ key: z.string(), value: z.string() })),
      about: z.array(z.object({ key: z.string(), value: z.string() })),
      aboutImages: z.array(
        z.object({
          url: z.union([z.string(), image()]),
          alt: z.string(),
        })
      ),
      amenities: z.array(z.object({ key: z.string(), value: z.string() })),
      amenitiesImages: z.array(
        z.object({
          url: z.union([z.string(), image()]),
          alt: z.string(),
        })
      ),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      video: z.object({
        url: z.string(),
      }),
    }),
});

const posts = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/posts" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.date(),
      description: z.string(),
      author: z.string(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      avatar: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

const rent = defineCollection({
  loader: async () => [],
  schema: z.object({}),
});

export const collections = {
  agents,
  sale,
  posts,
  legal,
  rent,
};
