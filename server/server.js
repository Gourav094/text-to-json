const express = require('express');
const app = express();

const PORT = process.env.PORT || 3000;

app.use(express.json());

const profile_extractor = async (text, retries) => {
    try{
        const response = await fetch("http://localhost:8000/llm/extract/profiles", {
            method: "POST",
            headers: {"Content-Type" : "application/json"},
            body: JSON.stringify({text, retries})
        })
        return await response?.json();
    }
    catch{
        console.log("Error from LLM service in generating json");
        return null;
    }
}


const project_extractor = async (text, retries) => {
    try{
        const response = await fetch("http://localhost:8000/llm/extract/project", {
            method: "POST",
            headers: {"Content-Type" : "application/json"},
            body: JSON.stringify({text, retries})
        })
        return await response?.json();
    }
    catch{
        console.log("Error from LLM service in generating json");
        return null;
    }
}

const extractors = {
    profile: profile_extractor,
    project: project_extractor
}

app.post("/analysis", async (req,res) => {
    const {text, retries} = req.body;
    try{
        const response = await fetch("http://localhost:8000/intents", {
            method: 'POST',
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({text, retries})
        })
        const {intents} = await response.json();

        if (!Array.isArray(intents)) {
            return res.status(400).json({ error: "Invalid intent response" });
        }

        const tasks = intents.filter(i => extractors[i])
                            .map(intent => extractors[intent](text, retries).then(data => [intent, data]))
        
        let result = await Promise.all(tasks);
        return res.status(200).json(Object.fromEntries(result));
    }
    catch(e){
        console.log(`Error from LLM ${e}`);
        return res.status(500).json({error: "Intent processing failed."});
    }
})


app.get("/", (req, res) => {
    res.json("Welcome to JSON extractor applicaiton!");
})

app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`)
})