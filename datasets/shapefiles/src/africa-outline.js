import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { open } from "shapefile";
import { getKey } from "../index.js";

/**
 * Write the django commands to a file handle that's passed in
 * @param {import("node:fs/promises").FileHandle} fileHandle A file handle to write to
 * @returns {Promise<void>}
 */
export async function writeToFile(fileHandle) {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);
  const shapeFilePath = resolve(__dirname, "../africa-outline/africa-outline.shp");
  const dbfFilePath = resolve(__dirname, "../africa-outline/africa-outline.dbf");

  // Open the shapefile and get the features keys
  const { value: feature } = await open(shapeFilePath, dbfFilePath).then((source) => source.read());

  const parentCode = getKey(feature.properties, "PTR");
  const region = getKey(feature.properties, "REGION");
  const code = getKey(feature.properties, "code");
  const area = getKey(feature.properties, "Shape_Area");

  // Compose the python manage.py command
  const command = `python manage.py loadshp --create-hierarchy \
./datasets/shapefiles/africa-outline/africa-outline.shp \
${region}=name,${code}=code,${parentCode}=parent_code,${area}=area \
Africa \
Continent \
Climate`;

  //   Write the python manage.py command to the sh file
  return fileHandle.write(`${command}\n`);
}
