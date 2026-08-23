import { defineCollection, z } from "astro:content";

const integrations = defineCollection({
  schema: ({ image }) =>
    z.object({
      integration: z.string(),
      description: z.string(),
      email: z.string(),
      permissions: z.array(z.string()),
      details: z.array(
        z.object({
          title: z.string(),
          value: z.string(),
          url: z.string().optional(),
        })
      ),
      logo: z.object({
        url: image(), //  Now validated by Astro
        alt: z.string(),
      }),
    }),
});

const jobs = defineCollection({
  schema: z.object({
    page: z.string(),
    details: z.record(z.string()),
  }),
});

const team = defineCollection({
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string(),
      intro: z.string(),
      education: z.array(z.string()),
      experience: z.array(z.string()),
      avatar: z.object({
        url: image(), //  Now validated by Astro
        alt: z.string(),
      }),
    }),
});

const customers = defineCollection({
  schema: ({ image }) =>
    z.object({
      customer: z.string(),
      challengesAndSolutions: z.array(
        z.object({
          title: z.string(),
          content: z.string(),
        })
      ),
      results: z.array(z.string()),
      about: z.string(),
      details: z.record(z.string()),
      logo: z.object({
        url: image(), //  Now validated by Astro
        alt: z.string(),
      }),
    }),
});

const changelog = defineCollection({
  schema: ({ image }) =>
    z.object({
      page: z.string(),
      description: z.string(),
      pubDate: z.date(),
      image: z.object({
        url: image(), //  Now validated by Astro
        alt: z.string(),
      }),
    }),
});

const helpcenter = defineCollection({
  schema: z.object({
    page: z.string(),
    description: z.string(),
  }),
});

const legal = defineCollection({
  schema: z.object({
    page: z.string(),
    pubDate: z.date().optional(),
  }),
});

const whitepaper = defineCollection({
  schema: z.object({
    page: z.string(),
    pubDate: z.date().optional(),
  }),
});

const posts = defineCollection({
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.date(),
      description: z.string(),
      author: z.string(),
      image: z.object({
        url: image(), //  Now validated by Astro
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

export const collections = {
  integrations,
  jobs,
  team,
  customers,
  changelog,
  helpcenter,
  legal,
  whitepaper,
  posts,
};
