// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract OGMarketBotHub {
    address public immutable owner;

    event StoragePurchased(
        address indexed buyer,
        uint256 indexed providerId,
        uint256 amountGb,
        uint256 durationMonths,
        string route,
        uint256 value,
        uint256 timestamp
    );

    event ComputePurchased(
        address indexed buyer,
        uint256 indexed providerId,
        uint256 vcpuHours,
        string route,
        uint256 value,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "owner only");
        _;
    }

    constructor(address initialOwner) {
        require(initialOwner != address(0), "owner required");
        owner = initialOwner;
    }

    function buyStorage(
        uint256 providerId,
        uint256 amountGb,
        uint256 durationMonths,
        string calldata route
    ) external payable {
        require(msg.value > 0, "value required");
        require(amountGb > 0, "amount required");
        require(durationMonths > 0, "duration required");
        emit StoragePurchased(
            msg.sender,
            providerId,
            amountGb,
            durationMonths,
            route,
            msg.value,
            block.timestamp
        );
    }

    function buyCompute(
        uint256 providerId,
        uint256 vcpuHours,
        string calldata route
    ) external payable {
        require(msg.value > 0, "value required");
        require(vcpuHours > 0, "amount required");
        emit ComputePurchased(
            msg.sender,
            providerId,
            vcpuHours,
            route,
            msg.value,
            block.timestamp
        );
    }

    function withdraw(address payable to, uint256 amount) external onlyOwner {
        require(to != address(0), "recipient required");
        require(amount <= address(this).balance, "insufficient balance");
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "withdraw failed");
    }
}
