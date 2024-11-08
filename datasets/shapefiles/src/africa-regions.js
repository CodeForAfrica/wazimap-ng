import { convert } from "geojson2shp";
import { glob } from "glob";
import { mkdir } from "node:fs/promises";
import { extname } from "node:path";
import { Readable } from "node:stream";
import { open as openShapefile } from "shapefile";
import { WritableStreamBuffer } from "stream-buffers";
import { Extract } from "unzip-stream";
import { getKey } from "../index.js";

// Function to get .shp and .dbf files from a directory
const getShapefiles = async (pattern) => {
  const files = await glob(pattern);
  return files.filter((file) => [".shp", ".dbf"].includes(extname(file)));
};

/**
 * Write the python manage.py commands to a file handle
 * @param {import("fs/promises").FileHandle} fileHandle The file handle to write to
 * @return {Promise<void>}
 */
export async function writeToFile(fileHandle) {
  // Get all .shp and .dbf files from the specified pattern
  const regionShapefiles = await getShapefiles("./countries-regions/*/{,modified/}*");

  // Group the files by their base name (without extension)
  const groupedFiles = regionShapefiles.reduce((acc, file) => {
    const baseName = file.slice(0, -4); // Remove the last 4 characters (.shp or .dbf)
    if (!acc[baseName]) {
      acc[baseName] = [];
    }
    acc[baseName].push(file);
    return acc;
  }, {});

  // For each group of files, open the shapefile and dbf file and read the features
  // then group the features by their baseName and level
  const shapefileFeatureMap = new Map();
  for (const [baseName, files] of Object.entries(groupedFiles)) {
    const [shpFile, dbfFile] = files;
    const source = await openShapefile(shpFile, dbfFile);
    let result = await source.read();
    while (!result.done) {
      const feature = result.value;
      const regionLevelKey = getKey(feature.properties, "ENGTYPE_1") ?? getKey(feature.properties, "Region");

      const regionLevel = feature.properties[regionLevelKey];
      if (!regionLevel) {
        console.warn(`No region level found for feature ${JSON.stringify(feature)} in ${baseName}`);
        result = await source.read();
        continue;
      }

      if (!shapefileFeatureMap.has(baseName)) {
        shapefileFeatureMap.set(baseName, new Map());
      }
      if (!shapefileFeatureMap.get(baseName).has(regionLevel)) {
        shapefileFeatureMap.get(baseName).set(regionLevel, []);
      }
      shapefileFeatureMap.get(baseName).get(regionLevel).push(feature);

      // Read the next feature
      result = await source.read();
    }
  }

  // Rebuild the shapefiles into a generated folder with the same structure as the source
  // The shapefiles will be split into multiple files based on the region Level
  // TODO: Muma. Because these promises are independent, consider using Promise.all for performance
  for (const [baseName, regionLevelMap] of shapefileFeatureMap) {
    const outputDir = `generated/${baseName}`;
    await mkdir(outputDir, { recursive: true });

    if (regionLevelMap.size > 1) {
      console.log(`${baseName} shapefile has multiple region types, splitting into multiple files`);
    }

    for (const [regionLevel, features] of regionLevelMap) {
      const zipFileWritableStream = new WritableStreamBuffer();
      await convert(features, zipFileWritableStream);
      await new Promise((resolve, reject) => {
        Readable.from(zipFileWritableStream.getContents())
          .pipe(Extract({ path: `${outputDir}/${regionLevel}` }))
          .on("finish", resolve)
          .on("error", reject);
      });
    }
  }

  // Read the generated shapefiles and write the python manage.py commands to the file handle
  const generatedShapefiles = await getShapefiles("generated/countries-regions/**/*.shp");
  for (const shapeFile of generatedShapefiles) {
    const dbfFile = shapeFile.replace(".shp", ".dbf");
    const { value: feature } = await openShapefile(shapeFile, dbfFile).then((source) => source.read());

    const parentCode = getKey(feature.properties, "parent_cod");
    const name = getKey(feature.properties, "Name") ?? getKey(feature.properties, "NAME");
    const code = getKey(feature.properties, "code");
    const area = getKey(feature.properties, "area");
    const levelKey = getKey(feature.properties, "ENGTYPE_1") ?? getKey(feature.properties, "Region");
    const level = feature.properties[levelKey].replace(/[^a-zA-Z0-9]/g, "");

    const command = `python manage.py loadshp \
"./datasets/shapefiles/${shapeFile}" \
${name}=name,${code}=code,${parentCode}=parent_code,${area}=area \
Africa \
"${level}" \
Climate`;

    // Write the python manage.py commands to the file handle
    await fileHandle.write(`${command}\n`);
  }
}
