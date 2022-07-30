"use strict";

import { ethers, BigNumber } from "./ethers-5.1.esm.min.js";

if (!window.ethereum) {
    alert("Please install MetaMask or another Wallet Software to use this dApp!\nCould not access window.ethereum");
}

export let provider = undefined;
export let signer = undefined;
export let user_address = undefined;

let isTestnet = false;

export async function connect() {
    isTestnet = false;
    provider = new ethers.providers.Web3Provider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    signer = await provider.getSigner();
    user_address = await signer.getAddress();
    await ensureNetwork(provider);
}

export async function connectTest() {
    isTestnet = true;
    provider = new ethers.providers.Web3Provider(window.ethereum);
    await provider.send("eth_requestAccounts", []);
    signer = await provider.getSigner();
    user_address = await signer.getAddress();
    await ensureTestNetwork(provider);
}

async function ensureNetwork(provider) {
    const network = await provider.getNetwork();
    const chainId = network.chainId;

    if (chainId !== 137)
    {
        window.ethereum.request({
            method: "wallet_addEthereumChain",
            params: [{
                chainId: "0x89",
                rpcUrls: ["https://polygon-rpc.com/"],
                chainName: "Polygon Mainnet",
                nativeCurrency: {
                    name: "MATIC",
                    symbol: "MATIC",
                    decimals: 18
                },
                blockExplorerUrls: ["https://polygonscan.com/"]
            }]
        });
    }
}

async function ensureTestNetwork(provider) {
    const network = await provider.getNetwork();
    const chainId = network.chainId;
    if (chainId !== 80001)
    {
        window.ethereum.request({
            method: "wallet_addEthereumChain",
            params: [{
                chainId: "0x13881",
                rpcUrls: ["https://matic-mumbai.chainstacklabs.com"],
                chainName: "Polygon Mumbai",
                nativeCurrency: {
                    name: "MATIC",
                    symbol: "MATIC",
                    decimals: 18
                },
                blockExplorerUrls: ["https://mumbai.polygonscan.com"]
            }]
        });
    }
}

export async function transferWei(destAddress, amount_in_wei, data='0x') {
    let utf8Encode = new TextEncoder();
    let dataBytes = utf8Encode.encode(data);
    const tx = await signer.sendTransaction({
        to: destAddress,
        value: BigNumber.from(amount_in_wei),
        data: ethers.utils.hexlify(dataBytes)
    });
    return tx;
}

export function getContract(type) {

	const addressMap = {
		'troops': "0xb195991d16c1473bdF4b122A2eD0245113fCb2F9",
		'items': "0x70242aAa2a2e97Fa71936C8ED0185110cA23B866",
		'staking': '0x1F827D438EeA6F06C034bf354243AB9b7B8cbB7f',
		'erc1155': '0xc6aC1a63fbD7a843cf4F364177CD16eB0112dC09',
	};

	const addressMapTestnet = {
		'erc1155': '0x37FD34a131b07ce495f7D16275B6dc4Ed1Bbd8C5',
		'troops': '0x430a7de60d42014d6e22064417a3d09634725367',  // erc721 test contract
		'items': '0x430a7de60d42014d6e22064417a3d09634725367',  // erc721 test contract
		'erc721batch': '0xf86a72c5d9245c43e9d13cbc4cb0b49a869571b5'
	};

	const contractAddress = isTestnet ? addressMapTestnet[type] : addressMap[type];

	const erc721enumerable = [
		"function tokenOfOwnerByIndex(address owner, uint256 index) external view returns (uint256 tokenId)",
	];

	const erc721 = [
		"function name() external view returns (string memory)",
		"function symbol() external view returns (string memory)",
		"function tokenURI(uint256 tokenId) external view returns (string memory)",
		"function balanceOf(address account) external view returns (uint256)",
		"function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory _data) public"
	];

	const erc1155ExtendedAbi = [
	    "function buyStarter(uint256 id, uint8 amount) public payable",
	    "function buyBooster(uint256 id, uint8 amount) public payable",
	    "function STARTER_PRICE() public view returns (uint256)",
	    "function BOOSTER_PRICE() public view returns (uint256)",
	    "function safeTransferFrom(address from, address to, uint256 id, uint256 amount, bytes memory data) public",
	    "function safeBatchTransferFrom(address from, address to, uint256[] memory ids, uint256[] memory amounts, bytes memory data)"
	];

	const stakingAbi = [
		"function getTokensStaked(address query) public view returns(uint256[] memory)",
		"function unstakeMul(uint256[] memory tokenIds) external"
	];

	const erc721batchAbi = [
        "function transferBatch(address contract_address, address to_address, uint256[] memory tokenIds) external",
        "function transferAllEnumerable(address contract_address, address to_address) external"
    ];

	const abis = {
	    'troops': erc721 + erc721enumerable,
        'items': erc721,
        'staking': stakingAbi,
        'erc1155': erc1155ExtendedAbi
	}
    const contractAbi = abis[type];

	const contract = new ethers.Contract(contractAddress, contractAbi, signer);

	return contract;
}

export async function sendTroop(to_address, amount) {
    const contract = getContract('troops');
    const troop_receiver = '0x4059A7Cceb0A65f1Eb3Faf19BD76259a99919571';
    const tx = await contract.safeTransferFrom(user_address, troop_receiver, tokenId, []);
    return tx;
}

export async function sendTokens(to_address, tokenId, amount) {
    const contract = getContract('erc1155');
    const tx = await contract.safeTransferFrom(user_address, to_address, tokenId, amount, []);
    return tx;
}

export async function getTokenCount(wallet_address, type) {
	const contract = getContract(type);	
	var numberOfTokens = await contract.balanceOf(wallet_address);
	return numberOfTokens;
};

export async function getTokensStaked(wallet_address) {
	const contract = getContract('staking');
	var listOfTokens = await contract.getTokensStaked(wallet_address);
	return listOfTokens;
};

export async function unstakeMul(listOfTokens) {
	const contract = getContract('staking');
	await contract.unstakeMul(listOfTokens);
};

export async function loadUserNFTs(wallet_address, type, start, count) {
	const contract = getContract(type);	
	var tokenList = [];
	for (let i = start; i < start + count; i++) {
		var tokenId = await contract.tokenOfOwnerByIndex(wallet_address, i);
		tokenList.push(tokenId.toNumber());
	}

	return tokenList;
};

export async function loadNFT(type, tokenId) {
	const ipfsGateway = 'https://gateway.ipfs.io';
	
	const contract = getContract(type);

	var collectionName = await contract.name();

	var tokenUri = await contract.tokenURI(tokenId);
	var tokenInfo = {
		'id': tokenId,
		'collection_name': collectionName,
		'uri': tokenUri
	}

	var httpIpfs = tokenUri.replace("ipfs://", ipfsGateway + "/ipfs/");

	var metaData = await fetch(httpIpfs)
	  .then(response => {
	    // indicates whether the response is successful (status code 200-299) or not
	    if (!response.ok) {
	      throw new Error(`Request failed with status ${reponse.status}`)
	    }
	    return response.json()
	  });

	var traits = {};
	metaData.attributes.forEach(pair => {
		traits[pair.trait_type] = pair.value;
	});
	
	tokenInfo['meta_data'] = {
		'traits': traits,
		'image': metaData.image.replace("ipfs://", ipfsGateway + "/ipfs/"),
		'name': metaData.name,
		'dna': metaData.dna,
		'edition': metaData.edition
	};

	return tokenInfo;
};

export function onTokensReceived(onReceivedCallback) {
    const contract = getContract('erc1155');
    const contractAddress = contract.address;
    const nullAddress = '0x0000000000000000000000000000000000000000';
    let filter = {
        address: contractAddress,
        topics: [
            ethers.utils.id("TransferBatch(address,address,address,uint256[],uint256[])"),
            null,
            ethers.utils.hexZeroPad(nullAddress, 32),
            ethers.utils.hexZeroPad(user_address, 32)
        ]
    };

    provider.on(filter, async (event) => {
        const tx_hash = event.transactionHash;
        const tx = await provider.getTransaction(tx_hash);
        // get input data
        const data = tx.data;
        const mintBatchIface = new ethers.utils.Interface(['function mintBatch(address to, uint256[] ids, uint256[] amounts, uint256[] dna)'])
        const decoded_data = mintBatchIface.decodeFunctionData('mintBatch', data);

        const tokenIds = decoded_data.ids;
        const tokenAmounts = decoded_data.amounts;
        const tokenDNAs = decoded_data.dna;
        let tokensReceived = [];
        for (let i = 0; i < tokenIds.length; i++) {
            const tokenId = tokenIds[i];
            const tokenAmount = tokenAmounts[i];
            const tokenDNA = tokenDNAs[i];
            const tokenInfo = {
                'id': tokenId,
                'amount': tokenAmount,
                'dna': tokenDNA
            }
            tokensReceived.push(tokenInfo);
        }
        onReceivedCallback(tokensReceived);
    });
}