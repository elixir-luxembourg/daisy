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

            // First Rule
            {
                test: /\.(tsx?)$/,
                exclude: /node_modules/,
                use: ["babel-loader"]
            },
        ]
    },
};