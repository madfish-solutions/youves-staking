import dotenv from "dotenv";
import { resolve } from "path";
dotenv.config({ path: resolve(__dirname, "..", "..", ".env") });
dotenv.config();

module.exports = {
  alice: {
    pkh: "tz1VSUr8wwNhLAzempoch5d6hLRiTh8Cjcjb",
    sk: "edsk3QoqBuvdamxouPhin7swCvkQNgq4jP5KZPbwWNnwdZpSpJiEbq",
    pk: "edpkvGfYw3LyB1UcCahKQk4rF2tvbMUk8GFiTuMjL75uGXrpvKXhjn",
  },
  bob: {
    pkh: "tz1aSkwEot3L2kmUvcoxzjMomb9mvBNuzFK6",
    sk: "edsk3RFfvaFaxbHx8BMtEW1rKQcPtDML3LXjNqMNLCzC3wLC1bWbAt",
    pk: "edpkurPsQ8eUApnLUJ9ZPDvu98E8VNj4KtJa1aZr16Cr5ow5VHKnz4",
  },
  carol: {
    pkh: "tz1MnmtP4uAcgMpeZN6JtyziXeFqqwQG6yn6",
    sk: "edsk3Sb16jcx9KrgMDsbZDmKnuN11v4AbTtPBgBSBTqYftd8Cq3i1e",
    pk: "edpku9qEgcyfNNDK6EpMvu5SqXDqWRLuxdMxdyH12ivTUuB1KXfGP4",
  },
  dev: {
    pkh: process.env.DEV_PKH,
    sk: process.env.DEV_SK,
    pk: "",
  },
  mainnetDeployer: {
    pkh: process.env.MAINNET_DEPLOYER_PKH,
    sk: process.env.MAINNET_DEPLOYER_SK,
    pk: "",
  },
};
