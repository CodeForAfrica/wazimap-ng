import { open } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { writeToFile as writeAfricaCountriesToFile } from "./src/africa-countries.js";
import { writeToFile as writeAfricaOutlineToFile } from "./src/africa-outline.js";
import { writeToFile as writeAfricaRegionsToFile } from "./src/africa-regions.js";

// Retrieve a key from an object if it exists else return null
export const getKey = (obj, key) => (Object.hasOwn(obj, key) ? key : null);

// Create an sh file to run the python manage.py commands
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const shapeFilePath = resolve(__dirname, "../../load_shapefiles.sh");

const loadShapefilesHandler = await open(shapeFilePath, "w");
await loadShapefilesHandler.write("#!/bin/bash\n\n");

// Africa Outline
await writeAfricaOutlineToFile(loadShapefilesHandler);

// Africa Countries
await writeAfricaCountriesToFile(loadShapefilesHandler);

// Africa Regions
await writeAfricaRegionsToFile(loadShapefilesHandler);

// Close the file handle
await loadShapefilesHandler.close();
