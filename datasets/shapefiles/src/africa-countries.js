import { convert } from "geojson2shp";
import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { Readable } from "node:stream";
import { fileURLToPath } from "node:url";
import { open as openShapefile } from "shapefile";
import { WritableStreamBuffer } from "stream-buffers";
import { Extract } from "unzip-stream";
import { getKey } from "../index.js";

/**
 * Write the python manage.py commands to a file handle
 * @param {import("fs/promises").FileHandle} fileHandle The file handle to write to
 * @return {Promise<void>}
 */
export async function writeToFile(fileHandle) {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);

  const shapeFilePath = resolve(__dirname, "../africa-countries/africa-shapefile.shp");
  const dbfFilePath = resolve(__dirname, "../africa-countries/africa-shapefile.dbf");

  // Open the shapefile and fix togo
  // **Fix Togo, code should be TG and not TGO.**
  // **The togo fix should not be needed when the file is fixed**
  // Get the features and load the keys
  const features = [];
  const source = await openShapefile(shapeFilePath, dbfFilePath);
  let result = await source.read();
  while (!result.done) {
    const feature = result.value;
    if (feature.properties.GID_0 === "TGO") {
      feature.properties.GID_0 = "TG";
    }
    // Fix the level while we're at it
    feature.properties.level = "Country";
    features.push(feature);
    result = await source.read();
  }

  // Write the generated zip files to a buffer instead of a file
  // Unzip the stream to the output directory to produce the individual files
  const outputDir = "generated/africa-countries";
  await mkdir(outputDir, { recursive: true });

  const zipfileWritableStream = new WritableStreamBuffer();
  await convert(features, zipfileWritableStream);
  await new Promise((resolve, reject) => {
    Readable.from(zipfileWritableStream.getContents())
      .pipe(Extract({ path: outputDir }))
      .on("finish", resolve)
      .on("error", reject);
  });

  // Load the fixed shapefile, read the feature keys and compose the python manage.py command
  const shapeFile = `${outputDir}/features.shp`;
  const dbfFile = shapeFile.replace(".shp", ".dbf");

  const { value: feature } = await openShapefile(shapeFile, dbfFile).then((source) => source.read());
  const parentCode = getKey(feature.properties, "parent_cod");
  const name = getKey(feature.properties, "COUNTRY");
  const code = getKey(feature.properties, "GID_0");
  const area = getKey(feature.properties, "area");

  // Compose the python manage.py command
  const command = `python manage.py loadshp \
"./datasets/shapefiles/${shapeFile}" \
${name}=name,${code}=code,${parentCode}=parent_code,${area}=area \
Africa \
Country \
Climate`;

  // Write the python manage.py command to the sh file
  return fileHandle.write(`${command}\n`);
}
