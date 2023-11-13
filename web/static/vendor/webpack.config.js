const webpack = require("webpack");

module.exports = {
    mode: "production",
    entry: {
        notification: "./components/notification/index_notif.tsx",
    },
    output: {
        filename: "../../js/[name].bundle.js"
    },
    resolve: {
        extensions: [".tsx", ".ts", ".jsx", ".js"]
    },
    devtool: "inline-source-map",
    module: {
        rules: [

            // First Rule: JavaScript JS/JSX files
            {
                test: /\.(jsx?)$/,
                exclude: /node_modules/,
                use: ["babel-loader"]
            },
            // Second Rule: TypeScript TS/TSX files
            {
                test: /\.(tsx?)$/,
                exclude: /node_modules/,
                use: ["ts-loader"]
            },
            // Third rule: Image files
            {
                test: /\.(gif|png|jpg|jpeg)$/,
                exclude: /node_modules/,
                type: "asset/resource"
            }
        ]
    },
};