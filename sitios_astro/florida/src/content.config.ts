import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

const legal = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/legal" }),
  schema: z.object({
    page: z.string(),
    pubDate: z.coerce.date(),
  }),
});

const customers = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/customers" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      avatar: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      location: z.string().optional(),
      occupation: z.string().optional(),
      course: z.string(),
      quote: z.string(),
      testimonial: z.string(),
    }),
});

const projects = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/projects" }),
  schema: ({ image }) =>
    z.object({
      pubDate: z.coerce.date(),
      title: z.string(),
      description: z.string(),
      live: z.string(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
    }),
});

const team = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/team" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string().optional(),
      bio: z.string().optional(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      socials: z
        .object({
          twitter: z.string().optional(),
          website: z.string().optional(),
          linkedin: z.string().optional(),
          email: z.string().optional(),
        })
        .optional(),
    }),
});

const posts = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/posts" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      pubDate: z.coerce.date(),
      description: z.string(),
      team: z.string(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      tags: z.array(z.string()),
    }),
});

const courses = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/courses" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      description: z.string(),
      pubDate: z.coerce.date(),
      teacher: z.string(),
      duration: z.string(),
      videoUrl: z.string(),
      price: z.number().min(0),
      skills: z.array(z.string()),
      sections: z.array(
        z.object({
          title: z.string(),
          lessons: z.array(z.string()),
        })
      ),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      tags: z.array(z.string()).optional(),
      isFeatured: z.boolean().optional(),
      isFree: z.boolean().optional(),
      isNew: z.boolean().optional(),
      isLocked: z.boolean().optional(),
    }),
});

const lessons = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/lessons" }),
  schema: z.object({
    title: z.string(),
    duration: z.string(),
    videoUrl: z.string(),
    course: z.string(),
    section: z.string(),
    isLocked: z.boolean().optional(),
  }),
});

const teachers = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/teachers" }),
  schema: ({ image }) =>
    z.object({
      name: z.string(),
      role: z.string(),
      org: z.string().optional(),
      bio: z.string(),
      image: z.object({
        url: z.union([z.string(), image()]),
        alt: z.string(),
      }),
      socials: z
        .object({
          twitter: z.string().optional(),
          linkedin: z.string().optional(),
          website: z.string().optional(),
        })
        .optional(),
    }),
});

export const collections = {
  team,
  courses,
  lessons,
  teachers,
  projects,
  customers,
  legal,
  posts,
};
