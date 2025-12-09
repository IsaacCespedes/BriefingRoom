import adapter from "@sveltejs/adapter-node";
import sveltePreprocess from "svelte-preprocess";

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: sveltePreprocess({
		compilerOptions: {
			accessors: process.env.VITEST === "true",
		},
	}),
	kit: {
		adapter: adapter(),
	},
};

export default config;
