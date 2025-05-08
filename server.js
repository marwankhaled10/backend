import express from "express";
import cors from "cors";
import fs from "fs";
import path, { dirname } from "path";
import csv from "csv-parser";
import { fileURLToPath } from "url"; 
import connectDB from "./connections.js";
import authRoutes from './routes/auth.js';

// Fix __dirname for ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 5005;

app.use(cors());
app.use(express.json());
app.use('/auth', authRoutes);

let medicines = [];
let categories = [];
let products = [];
let wishlist = [];

async function fetchAndProcessCSV() {
  try {
    console.log(" Reading local CSV data...");

    const results = [];
    const filePath = path.join(__dirname, "finaldatasets.csv");

    await new Promise((resolve, reject) => {
      fs.createReadStream(filePath)
        .pipe(csv({ mapHeaders: ({ header }) => header.trim() }))
        .on("data", (data) => results.push(data))
        .on("end", () => {
          console.log(` Processed ${results.length} records from CSV`);
          resolve();
        })
        .on("error", (error) => reject(error));
    });

    if (results.length === 0) {
      console.error(" CSV loaded but no rows found.");
      return;
    }

    processData(results);
    console.log(" Data processing complete");
    console.log(` Categories: ${categories.length}`);
    console.log(` Medicines: ${medicines.length}`);
    console.log(` Products: ${products.length}`);
  } catch (error) {
    console.error(" Error processing CSV:", error);
  }
}

function processData(rawData) {
  const uniqueCategories = [...new Set(rawData.map((item) => item.Category).filter(Boolean))];

  categories = uniqueCategories.map((categoryName, index) => {
    const prefix = categoryName.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
    return {
      id: index + 1,
      title: categoryName,
      prefix,
      img: `https://via.placeholder.com/150?text=${encodeURIComponent(categoryName)}`
    };
  });

  medicines = rawData.map((item, index) => {
    const category = categories.find((cat) => cat.title === item.Category);
    return {
      id: index + 1,
      name: item.Trade_Name || "Unknown Medicine",
      price: item.Price || "0.00",
      category: category ? category.prefix : "uncategorized",
      image: item.Image_URL || `https://via.placeholder.com/150?text=${encodeURIComponent(item.Trade_Name || "Medicine")}`,
      dosage: item.Dosage_Form ? `${item.Quantity_of_Dosage_Form || "1"} ${item.Dosage_Form}` : "N/A",
      manufacturer: item["Local/Import"] || "Unknown",
      description: item.Indications_for_Use || item.Generic_Name || "No description available",
      genericName: item.Generic_Name || "",
      sideEffects: [
        item.Side_Effect_1, item.Side_Effect_2, item.Side_Effect_3,
        item.Side_Effect_4, item.Side_Effect_5, item.Side_Effect_6,
        item.Side_Effect_7, item.Side_Effect_8, item.Side_Effect_9
      ].filter(Boolean)
    };
  });

  products = medicines.map((medicine) => ({
    id: String(medicine.id),
    title: medicine.name,
    cat_prefix: medicine.category,
    img: medicine.image,
    price: parseFloat(medicine.price) || 0,
    rating: parseFloat((Math.random() * 1.5 + 3.5).toFixed(1)),
    reviews: Math.floor(Math.random() * 200),
    discount: Math.random() < 0.3 ? Math.floor(Math.random() * 25) : 0
  }));
}

// ========== ROUTES ==========

app.get("/categories", (req, res) => res.json(categories));

app.get("/medicines", (req, res) => {
  const { category, q } = req.query;
  let filtered = medicines;

  if (category) {
    filtered = filtered.filter((m) => m.category === category);
  }

  if (q) {
    const searchTerm = q.toString().toLowerCase();
    filtered = filtered.filter(
      (m) =>
        m.name.toLowerCase().includes(searchTerm) ||
        m.manufacturer.toLowerCase().includes(searchTerm) ||
        m.description.toLowerCase().includes(searchTerm) ||
        m.genericName.toLowerCase().includes(searchTerm)
    );
  }

  res.json(filtered);
});

app.get("/products/search", (req, res) => {
  const query = req.query.q?.toLowerCase();
  if (!query) return res.status(400).json({ message: "Missing search query" });

  const results = products.filter((product) =>
    product.title.toLowerCase().includes(query)
  );

  res.json(results);
});

app.get("/products", (req, res) => {
  const { cat_prefix } = req.query;
  let filtered = products;

  if (cat_prefix) {
    filtered = filtered.filter((p) => p.cat_prefix === cat_prefix);
  }

  res.json(filtered);
});

app.get("/products/:id", (req, res) => {
  const productId = req.params.id;
  const product = products.find((p) => p.id === productId);

  if (!product) return res.status(404).json({ message: "Product not found" });

  const medicine = medicines.find((m) => m.id === parseInt(productId));

  if (!medicine) return res.json(product);

  const completeProduct = {
    id: product.id,
    name: product.title,
    image: product.img,
    price: product.price,
    rating: product.rating,
    reviews: product.reviews,
    discount: product.discount,
    category: medicine.category,
    description: medicine.description,
    stock: Math.floor(Math.random() * 50) + 5,
    manufacturer: medicine.manufacturer,
    genericName: medicine.genericName,
    dosage: medicine.dosage,
    sideEffects: medicine.sideEffects,
    features: [
      `Contains ${medicine.genericName || medicine.name}`,
      `${medicine.dosage} dosage form`,
      `Manufactured by ${medicine.manufacturer}`,
      "Quality tested and approved",
      "Stored in optimal conditions"
    ],
    usage: `Take as directed by your healthcare professional. ${medicine.dosage} form available.`,
    warnings: "Keep out of reach of children. Consult your doctor before use if you are pregnant, nursing, or have a medical condition.",
    ingredients: medicine.genericName || "Active and inactive ingredients listed on packaging.",
    faqs: [
      {
        question: `What is ${product.title} used for?`,
        answer: medicine.description || "Please consult with your healthcare provider for specific usage information."
      },
      {
        question: "Are there any side effects?",
        answer: medicine.sideEffects && medicine.sideEffects.length > 0
          ? `Possible side effects include: ${medicine.sideEffects.join(", ")}.`
          : "Side effects may occur. Please consult your healthcare provider or refer to the package insert for a complete list of side effects."
      },
      {
        question: "How should I store this medication?",
        answer: "Store at room temperature away from moisture and heat. Keep container tightly closed. Keep out of reach of children."
      }
    ]
  };

  res.json(completeProduct);
});

// ✅ ========== WISHLIST ROUTES ==========
app.get("/wishlist", (req, res) => {
  res.json(wishlist);
});

app.post("/wishlist", (req, res) => {
  const { id, name, price, image } = req.body;

  const exists = wishlist.find(item => item.id === id);
  if (exists) {
    return res.status(409).json({ message: "Item already in wishlist" });
  }

  const newItem = { id, name, price, image };
  wishlist.push(newItem);
  res.status(201).json({ message: "Added to wishlist", item: newItem });
});

app.delete("/wishlist/:id", (req, res) => {
  const itemId = req.params.id;
  const initialLength = wishlist.length;
  wishlist = wishlist.filter(item => item.id !== itemId);

  if (wishlist.length === initialLength) {
    return res.status(404).json({ message: "Item not found" });
  }

  res.json({ message: "Removed from wishlist" });
});

// ========== INIT ==========
async function initializeServer() {
  await fetchAndProcessCSV();
  app.listen(PORT, () => {
    console.log(` Server running at http://localhost:${PORT}`);
  });
}

connectDB();
initializeServer();
