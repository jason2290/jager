import 'dotenv/config';
import axios from 'axios';
import { ethers } from 'ethers';
import { Keypair } from '@solana/web3.js';
import nacl from 'tweetnacl';
import bs58 from 'bs58';
import fs from 'fs';
import csv from 'csv-parser';

// 獲取 EVM 地址
function getEvmAddress(privateKey) {
  try {
    const wallet = new ethers.Wallet(privateKey);
    return wallet.address;
  } catch (error) {
    throw new Error(`無效的 EVM 私鑰: ${error.message}`);
  }
}

// 獲取 Solana 地址
function getSolanaAddress(secretKey) {
  try {
    const keypair = Keypair.fromSecretKey(secretKey);
    return keypair.publicKey.toBase58();
  } catch (error) {
    throw new Error(`無效的 Solana 私鑰: ${error.message}`);
  }
}

// 生成 EVM 簽名
async function signEvmMessage(message, privateKey) {
  try {
    const wallet = new ethers.Wallet(privateKey);
    return await wallet.signMessage(message);
  } catch (error) {
    throw new Error(`EVM 簽名失敗: ${error.message}`);
  }
}

// 生成 Solana 簽名
function signSolanaMessage(message, secretKey) {
  try {
    const messageBuffer = Buffer.from(message);
    const keypair = Keypair.fromSecretKey(secretKey);
    const signature = nacl.sign.detached(messageBuffer, keypair.secretKey);
    return Buffer.from(signature).toString('base64');
  } catch (error) {
    throw new Error(`Solana 簽名失敗: ${error.message}`);
  }
}

// 發送 API 請求
async function sendBindRequest(evmAddress, solanaAddress, signStr, solSignStr) {
  const payload = {
    address: evmAddress,
    solAddress: solanaAddress,
    signStr: signStr,
    solSignStr: solSignStr
  };

  try {
    const response = await axios.post('https://api.jager.meme/api/airdrop/bindSolana', payload, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return { success: true, data: response.data };
  } catch (error) {
    return { success: false, error: error.response ? error.response.data : error.message };
  }
}

// 處理單組私鑰
async function processKeyPair(evmPrivateKey, solanaPrivateKey, index) {
  console.log(`\n處理第 ${index + 1} 組私鑰...`);

  try {
    // 推導地址
    const evmAddress = getEvmAddress(evmPrivateKey);
    console.log('EVM 地址:', evmAddress);

    const solSecretKey = bs58.decode(solanaPrivateKey);
    const solanaAddress = getSolanaAddress(solSecretKey);
    console.log('Solana 地址:', solanaAddress);

    // 生成簽名
    const evmMessage = evmAddress; // EVM 簽名訊息為 EVM 地址
    const solMessage = solanaAddress; // Solana 簽名訊息為 Solana 地址

    const signStr = await signEvmMessage(evmMessage, evmPrivateKey);
    const solSignStr = signSolanaMessage(solMessage, solSecretKey);
    
    // 發送請求
    const result = await sendBindRequest(evmAddress, solanaAddress, signStr, solSignStr);
    if (result.success) {
      const canAirdrop = result.data?.data?.airdrop?.canAirdrop ?? '未知';
      console.log(`第 ${index + 1} 組綁定成功｜是否有空投: ${canAirdrop}`);
    } else {
      console.error(`第 ${index + 1} 組失敗:`, result.error);
    }
  } catch (error) {
    console.error(`第 ${index + 1} 組處理失敗:`, error.message);
  }
}

// 從 CSV 讀取並批量處理
async function main() {
  const csvFilePath = './keys.csv'; // CSV 檔案路徑
  const keyPairs = [];

  // 讀取 CSV
  fs.createReadStream(csvFilePath)
    .pipe(csv())
    .on('data', (row) => {
      if (row.evmPrivateKey && row.solanaPrivateKey) {
        keyPairs.push({
          evmPrivateKey: row.evmPrivateKey.trim(),
          solanaPrivateKey: row.solanaPrivateKey.trim()
        });
      }
    })
    .on('end', async () => {
      console.log(`讀取到 ${keyPairs.length} 組私鑰`);

      // 按順序處理每組私鑰
      for (let i = 0; i < keyPairs.length; i++) {
        await processKeyPair(keyPairs[i].evmPrivateKey, keyPairs[i].solanaPrivateKey, i);
      }

      console.log('\n所有私鑰處理完成');
    })
    .on('error', (error) => {
      console.error('讀取 CSV 失敗:', error.message);
    });
}

// 執行
main();